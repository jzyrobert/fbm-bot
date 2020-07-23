import re

validurls = [
"https://www.facebook.com/marketplace/item/227462415226490/",
"https://www.facebook.com/marketplace/item/227462415226490",
"www.facebook.com/marketplace/item/227462415226490",
"www.facebook.com/marketplace/item/227462415226490/",
"facebook.com/marketplace/item/227462415226490",
"facebook.com/marketplace/item/227462415226490/",
"marketplace/item/227462415226490",
"marketplace/item/227462415226490/",
"https://m.facebook.com/marketplace/item/227462415226490",
"https://m.facebook.com/marketplace/item/227462415226490/",
"m.facebook.com/marketplace/item/227462415226490",
"m.facebook.com/marketplace/item/227462415226490/"
]

full_url_regex = re.compile("(https?:\/\/)?(www.)?(m.)?(facebook\.com\/)?marketplace\/item\/\d+/?")
url_id_regex = re.compile("marketplace\/item\/\d+")

pending_regex = re.compile("\"is_pending\":true")
sold_regex = re.compile("\"is_sold\":true")

content = "\"can_seller_change_availability\":false,\"most_recent_active_order_as_buyer\":null,\"order_summaries\":[],\"product_item\":{\"is_pending\":true,\"is_sold\":false,\"id\":\"3112691302111511\",\"boosted_marketplace_listing\":null,\"promoted_listing\":null},\"marketplace_listing_category_id\":\"1557869527812749\",\"should_show_txn_survey_on_mas\":false,\"inventory_count\":null,\"delivery_types\":[\"IN_PERSON\"],\"__isGroupCommerceProductItemIsDeprecated\":\"GroupCommerceProductIt"
for url in validurls:
    print(full_url_regex.search(url) != None)
    print(url_id_regex.search(url).group(0))

print(pending_regex.search(content) != None)
print(sold_regex.search(content) != None)