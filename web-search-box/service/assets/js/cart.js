
// Cart data.
var cItems = {};

cItems['d'] = {
  'spri_massage_ball': {
    'internal_name': 'spri_massage_ball',
    'amazon_link': 'http://www.amazon.com/gp/product/B00LY9L6BI?psc=1&redirect=true&ref_=oh_aui_detailpage_o06_s01',
    'img_link': 'http://ecx.images-amazon.com/images/I/71dgm-uaHEL._SL1500_.jpg',
    'display_name': 'SPRI Muscle Relief Ball',
    'price': 9.99,
  },
  'soma_massage_balls': {
    'internal_name': 'soma_massage_balls',
    'amazon_link': 'http://www.amazon.com/gp/product/B00Z23MLOI?psc=1&redirect=true&ref_=oh_aui_detailpage_o05_s00',
    'img_link': 'http://ecx.images-amazon.com/images/I/71t%2B8alXghL._SL1500_.jpg',
    'display_name': '5-Balls Trigger Point Release',
    'price': 34.99
  }
};


var cartTable = {};
cartTable.removeOne = function(item) {
  window.console.log('Removing ' + item);
  theCart.remove(item, 1);
  $('#cart-table').html('');
  cartTable.renderCartTable();
}
cartTable.rowTmplTxt =
          '<tr>' +
          '<td></td><td><%=display_name%></td>' +
          '<td>$<%=price%></td><td><%=quantity%></td>' +
          '<td>$<%=total_price%></td>' +
          '<td><button class="btn" onclick="ctrl.removeOne(\'<%=internal_name%>\');">' +
          'Remove one</button></td>' +
          '</tr>';
cartTable.rowTmpl = _.template(cartTable.rowTmplTxt);
cartTable.renderCartTable = function() {
      // Show items from the cart.
  var cart = theCart.getCart();
  var itemKeys = Object.keys(cart['items']);
  itemKeys.sort();
  var rows = [];
  for (var i = 0; i < itemKeys.length; i++) {
    var itemKey = itemKeys[i];
    var numItems = cart['items'][itemKey];
    window.console.log('Have ' + numItems + ' of ' + itemKey);
    var row = cItems['d'][itemKey];
    row['quantity'] = numItems;
    row['total_price'] = numItems * row['price'];
    // Add quantity
    // Add total = quantity * price per amount
    rows.push(row);
  }
  for (var i = 0; i < rows.length; i++) {
    var rowHtml = cartTable.rowTmpl(rows[i]);
    // Show items from cart.
    $('#cart-table').append(rowHtml);
  }
}

// Cart logic.

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

theCart.remove = function(item, amount) {
  var cart = theCart.getCart();
  var items = cart['items'];
  if ((item in items) == false) {
    return;
  }
  cart['num_items'] = cart['num_items'] - amount;
  items[item] = items[item] - amount;
  // If you have fewer than 0, you have 0 items and you
  // need to remove the item.
  if (cart['num_items'] < 0) {
    cart['num_items'] = 0;
  }
  if (items[item] <= 0) {
    // Remove the item
    delete items[item];
  }
  cart['items'] = items;
  theCart.updateCart(cart);
  theCart.refreshView();
}

theCart.addToCart = function(item) {
  var cart = theCart.getCart();
  cart['num_items'] = cart['num_items'] + 1;
  var items = cart['items'];
  if (item in items) {
    items[item] = items[item] + 1;
  } else {
    // first time user got this item.
    items[item] = 1;
  }
  cart['items'] = items;
  theCart.updateCart(cart);
  theCart.refreshView();
}