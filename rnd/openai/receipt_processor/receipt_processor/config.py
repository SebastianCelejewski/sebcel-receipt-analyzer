ALLOWED_CATEGORIES = {
    "wydatki codzienne",
    "wydatki tygodniowe",
    "lekarze i leczenie",
    "ubrania",
    "przejazdy",
    "paliwo",
    "inne"
}

SUMMARY_CSV_HEADERS = [
    "datetime",
    "store",
    "document_type",
    "total",
    "category"
]

DETAILS_CSV_HEADERS = [
    "datetime",
    "store",
    "document_type",
    "category",
    "subcategory",
    "original_item_name",
    "normalized_item_name",
    "unit",
    "unit_price",
    "amount",
    "price"
]