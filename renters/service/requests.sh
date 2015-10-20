set -e
#set -x

BASE_URL=http://localhost:8080
#BASE_URL=http://immense-badlands-3000.herokuapp.com

# Test when the user wants to know the price of the insurance.
curl -H "Content-Type: application/json" -X POST -d  '
{
    "renter_form": {
       "insurance_type": "renters",
       "first_name": "Christian",
       "last_name": "Bale",
       "dob": "01/30/1974",
       "address": "3328 Bay Road",
       "city": "Rewood City",
       "state": "CA",
       "zip_code": "94063",
       "purchase_category": "cheap"
    }
}' \
$BASE_URL/price

printf '\n-----------------------------------\n'

# Test when the user purchases insurance.
curl -H "Content-Type: application/json" -X POST -d  '
{
    "renter_form": {
       "insurance_type": "renters",
       "first_name": "Christian",
       "last_name": "Bale",
       "dob": "01/30/1974",
       "address": "3328 Bay Road",
       "city": "Rewood City",
       "state": "CA",
       "zip_code": "94063",
       "purchase_category": "medium"
    },
    "payment_form": {
      "billing_address": "766 Vaquero",
      "exp_year": "15",
      "exp_month": "06",
      "cvc": "323",
      "card_number": "232343534323"
    }
}' \
$BASE_URL/buy
