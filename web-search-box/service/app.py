import datetime, logging, os, sys, traceback, copy
import requests, util
from flask import Flask, render_template, json, jsonify, request, redirect, send_from_directory
from logging import StreamHandler, Formatter
from config import config
from models import RenterForm
from helper import *

sys.path.append("..") # Adds higher directory to python modules path.

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

log_handler = StreamHandler(sys.stdout)
app.logger.addHandler(log_handler)
log_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
log_err_handler = StreamHandler(sys.stderr)
log_err_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(log_err_handler)

# Displaying templates.
@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)

@app.route('/shop')
def shop():
    return util.render_common_template('shop.html')

@app.route('/view_cart')
def view_cart():
    return util.render_common_template('view_cart.html')

@app.route('/')
def home_page():
    return util.render_common_template('index.html')

accepted_words = frozenset([
  'wrist', 'pain',
  'poop', 'constipation',
  'anxiety', 'depression'
])

def remove_stopwords(q):
  words = q.split(' ')
  s = []
  for word in words:
    if word in accepted_words:
      s.append(word)
  return ' '.join(s)

def get_results(q):
  generic = [
  {'suggestion': 
    """We dont have help for that yet! Please help contribute to our database of problems to solve <a href="{name}" target="_blank">here</a>.
    """.format(name='https://docs.google.com/document/d/1lTk44VaD0rmLMCHbPUPJ2eg8xfRR0tj5l9ssehNzGQI/edit'), 
    'poster': 'Worry Free CO.'
  }]

  # Remove stop words. Then look up what is the appropriate diagnosis in our Google
  # Doc.
  d = {
    'wrist pain': 'https://docs.google.com/document/d/1gdWu1Bud_j7omTOZYulZAxVgg-M2U-LKXMnC3sL_gJs/edit',
    # Constipation
    'poop': 'https://docs.google.com/document/d/1BLasIf5rhg1DHweHNR0mQJalabW-CvLY7aAMwxUbaCs/edit',
    'constipation': 'https://docs.google.com/document/d/1BLasIf5rhg1DHweHNR0mQJalabW-CvLY7aAMwxUbaCs/edit',
    # Anxiety / depression
    'anxiety': 'https://docs.google.com/document/d/13TB5VoYIwol6M7NQANAjcLWMkPtkuChCphLjlwsCN9g/edit',
    'depression': 'https://docs.google.com/document/d/13TB5VoYIwol6M7NQANAjcLWMkPtkuChCphLjlwsCN9g/edit'
  }
  q_stripped = remove_stopwords(q)
  recommended_doc = d.get(q_stripped, None)
  if recommended_doc is None:
    return generic

  david_html = """
    Heres our definitive guide based on our many years of dealing with the same issue. <a href="{name}" target="_blank">(link)</a>
  """.format(name=recommended_doc)
  results = [
    {'suggestion': david_html, 'poster': 'David L.'},
    {'suggestion': 'Go see your nearest local doctor.', 'poster': 'Generic person'}
  ]
  return results


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    results = get_results(query)
    info = {
      'q': query,
      'results': results
    }
    return util.render_common_template('results.html', info=info)

@app.route('/quote', methods=['GET', 'POST'])
def quote_page():
    # The Amazon Elastic Load Balancer (ELB) supports a HTTP header called X-FORWARDED-PROTO.
    # All the HTTPS requests going through the ELB will have the value of X-FORWARDED-PROTO equal to 'HTTPS'.
    if request.headers.get('X-Forwarded-Proto') == 'http':
        secure_qoute = "https://rentsafe.co/quote"
        return redirect(secure_qoute, code=302)

    # Log what the user had regarding their email and first name.
    # (Do it by sending an email to us).
    first_name = request.form.get('first_name')
    email = request.form.get('email')
    founders = ['cl@rentsafe.co', 'dl@rentsafe.co', 'gc@rentsafe.co']
    util.send_simple_email(
      founders, 
      subject='{name} just entered Get a quote on rentsafe.co'.format(name=first_name), 
      body='Go follow up with {email}!'.format(email=email),
      from_person='dl@rentsafe.co')
    return util.render_common_template('quote.html', public_key=config.public_key)

@app.route('/payment_complete')
def payment_complete_page():
    return util.render_common_template('payment_complete.html')

@app.route('/terms')
def terms():
    return util.render_common_template('terms.html')

@app.route('/privacy_policy')
def privacy_policy():
    return util.render_common_template('privacy_policy.html')

@app.route('/about')
def about():
    return util.render_common_template('about.html')

#first name, last name, address, phone number, dob
@app.route('/buy', methods=['POST'])
def buy():
    """
      When the user has completed the flow and is completing their
      insurance purchase.

      Example input:
      form = {
       'insurance_type': 'Renters',
       'first_name': 'Christian',
       'last_name': 'Bale',
       'dob': '01/30/1974',
       'gender': 'm',
       'address': '3328 Bay Road',
       'city': 'Rewood City',
       'state': 'CA',
       'zip_code': '94063'
      }
    """
    try:
      data = request.get_json()
      token = None
      if data.get('payment_form', None):
          payment_form = data['payment_form']
          # Store payment information, get token and save it into renter_form_dict.
          headers = {'content-type': 'application/json'}

          try:
              r = requests.post(config.payment_endpoint, data=json.dumps(payment_form), headers=headers)
              result = r.json()
              if result['status'] == 'success':
                  app.logger.info("Success to store credit card info.")
                  token = result['token']
              else:
                  app.logger.error("Fail to store credicard. {message}".format(**result) )
                  return jsonify(status='fail', message="Invalid Credit Card Information")
          except Exception as e:
              app.logger.error("Fail to connect to payment service. %s" % e)

      memorized_price = get_price_of_user_form(data, use_memorized_only=True)
      app.logger.info("Get price of the form")
      # Expand defaults so we know what we are assuming.
      renter_form_dict = data['renter_form']
      defaults = ExpandDefaults(renter_form_dict['purchase_category'])
      renter_form_dict.update(defaults)
      # Log whatever price we have calculated here.
      renter_form_dict['policy_price'] = '$%.2f' % (memorized_price)
      learned_price = get_price_of_user_form(data, use_memorized_only=False)
      renter_form_dict['learned_policy_price'] = '$%.2f' % (learned_price)

      # Payment information
      renter_form = RenterForm(**renter_form_dict)
      renter_form.token = token
      renter_form.save()
      app.logger.info("Save the form to database")
      util.send_email([renter_form.email_address], 'Thank You for Trusting! Confirmation for Your Purchase!',
                      'email/confirmation.html', 'email/confirmation.txt', **renter_form_dict)
      return jsonify(status='success')

    except Exception as e:
      print(e)
      line = traceback.format_exc()
      return jsonify(status='fail', message=line)

@app.errorhandler(404)
def page_not_found(e):
    return util.render_common_template('errors/404.html'), 404

@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error(str(error))
    return util.render_common_template('errors/500.html', err_msg=repr(error))


if __name__ == '__main__':
    logging.basicConfig()
    if config.DEBUG:
        app.logger.setLevel(logging.DEBUG)
        app.run(debug=True, host='0.0.0.0', port=8080)
    elif config.PROD:
        app.logger.setLevel(logging.ERROR)
        from gevent.wsgi import WSGIServer

        http_server = WSGIServer(('0.0.0.0', 80), app)
        http_server.serve_forever()
