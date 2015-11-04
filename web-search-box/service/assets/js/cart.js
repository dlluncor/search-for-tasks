var cItems = {};

cItems['d'] = {
  'spri_massage_ball': {
    'amazon_link': 'http://www.amazon.com/gp/product/B00LY9L6BI?psc=1&redirect=true&ref_=oh_aui_detailpage_o06_s01',
    'display_name': 'SPRI Muscle Relief Ball',
    'price': 9.99,
  },
  'soma_massage_balls': {
    'amazon_link': 'http://www.amazon.com/gp/product/B00Z23MLOI?psc=1&redirect=true&ref_=oh_aui_detailpage_o05_s00',
    'display_name': '5-Balls Trigger Point Release',
    'price': 34.99
  }
};

var theCart = {};

theCart.clear = function() {
  localStorage.setItem('cart', null);
}

theCart.getCart = function() {
  return JSON.parse(localStorage.getItem('cart'));
}

theCart.updateCart = function(cart) {
  localStorage.setItem('cart', JSON.stringify(cart))
}

theCart.refreshView = function() {
  window.console.log('Initing number of items in cart.');
  var cart = localStorage.getItem('cart');
  if (cart == null || cart == "null") {
    cart = {
      'num_items': 0,
      'items': {}
    };
  } else {
    cart = JSON.parse(cart); 
  }
  window.console.log('Number of items in cart: ' + cart['num_items']);
  $('#items-in-cart').html(cart['num_items']);
  theCart.updateCart(cart);
}

theCart.addToCart = function(item) {
  var cart = theCart.getCart();
  cart['num_items'] = cart['num_items'] + 1;
  var items = cart['items'];
  if (items[item]) {
    items[item] = items[item] + 1;
  } else {
    // first time user got this item.
    items[item] = 0;
  }
  cart['items'] = items;
  theCart.updateCart(cart);
  theCart.refreshView();
}