from backend.app.common.config.column_names import COLUMNS, VALUES
FILTER_SETTINGS = {
    "category": {
        "column": COLUMNS["CATEGORY"],
        "value": VALUES["CLAIM_FROM_BANK"],
        "enabled": True,
        "type": "exact_match"
    },
    "methodOfProtection": {
        "column": COLUMNS["METHOD_OF_PROTECTION"],
        "value": VALUES["CLAIM_PROCEEDINGS"],
        "enabled": True,
        "type": "exact_match"
    }
}