from db_local import local_engine

def apply_delivery_merge_rule_293(rows):
    """
    293 납품처 합치기 규칙 적용
    - source_code/source_name → target_code/target_name
    """

    create_upload_delivery_merge_rule_table()

    with local_engine.connect() as conn:
        rules = conn.exec_driver_sql(
            """
            SELECT
                source_code,
                source_name,
                target_code,
                target_name
            FROM upload_delivery_merge_rule
            WHERE is_active = 1
            """
        ).mappings().all()

    rule_map = {
        rule["source_code"]: dict(rule)
        for rule in rules
        if rule["source_code"]
    }

    converted_rows = []

    for row in rows:
        row = dict(row)

        delivery_code = row.get("DELIVERY_CODE")

        if delivery_code in rule_map:
            rule = rule_map[delivery_code]

            row["BEFORE_MERGE_DELIVERY_CODE"] = row.get("DELIVERY_CODE")
            row["BEFORE_MERGE_DELIVERY_NAME"] = row.get("DELIVERY_NAME")

            row["DELIVERY_CODE"] = rule["target_code"]
            row["DELIVERY_NAME"] = rule["target_name"]

            row["MERGE_RULE_APPLIED"] = True
        else:
            row["BEFORE_MERGE_DELIVERY_CODE"] = ""
            row["BEFORE_MERGE_DELIVERY_NAME"] = ""
            row["MERGE_RULE_APPLIED"] = False

        converted_rows.append(row)

    return converted_rows


def create_upload_delivery_merge_rule_table():
    with local_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS upload_delivery_merge_rule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT,
                source_code TEXT,
                source_name TEXT,
                target_code TEXT,
                target_name TEXT,
                memo TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def apply_dispatch_upload_rules(rows):
    """
    291 제품명 자동변환
    292 납품처 분리
    293 납품처 합치기
    """
    rows = apply_product_name_rule_291_to_rows(rows)

    rows = apply_delivery_split_rule_292(rows)

    # rows = apply_delivery_merge_rule_293(rows)

    rows = add_applied_rule_labels(rows)

    rows = sort_applied_rules_first(rows)

    return rows

def apply_product_name_rule_291_to_rows(rows):
    with local_engine.connect() as conn:
        rules = conn.exec_driver_sql(
            """
            SELECT
                before_name,
                after_name
            FROM product_name_rule
            WHERE is_active = 1
            """
        ).mappings().all()

    rule_map = {
        rule["before_name"]: rule["after_name"]
        for rule in rules
        if rule["before_name"]
    }

    converted_rows = []

    for row in rows:
        row = dict(row)

        before_name = row.get("product_name", "")

        row["product_name_before_291"] = ""
        row["product_name_rule_291_applied"] = False

        if before_name in rule_map:
            row["product_name_before_291"] = before_name
            row["product_name"] = rule_map[before_name]
            row["product_name_rule_291_applied"] = True

        converted_rows.append(row)

    return converted_rows

def add_applied_rule_labels(rows):
    converted_rows = []

    for row in rows:
        row = dict(row)

        applied_rules = []

        if row.get("product_name_rule_291_applied"):
            applied_rules.append("291")

        if row.get("delivery_split_rule_292_applied"):
            applied_rules.append("292")
        if row.get("merge_rule_293_applied"):
            applied_rules.append("293")

        row["applied_rules"] = ", ".join(applied_rules)

        converted_rows.append(row)

    return converted_rows


def sort_applied_rules_first(rows):
    return sorted(
        rows,
        key=lambda row: (
            not bool(row.get("applied_rules")),
            row.get("delivery_name", ""),
            row.get("product_name", ""),
        )
    )

def apply_delivery_split_rule_292(rows):
    product_codes = sorted({
        row.get("product_code")
        for row in rows
        if row.get("product_code")
    })

    product_base_map = {}

    with local_engine.connect() as conn:
        if product_codes:
            placeholders = ",".join(["?"] * len(product_codes))

            result = conn.exec_driver_sql(
                f"""
                SELECT
                    code,
                    base_category
                FROM product
                WHERE code IN ({placeholders})
                """,
                tuple(product_codes)
            )

            product_base_map = {
                row["code"]: row["base_category"]
                for row in result.mappings().all()
            }

        rules = conn.exec_driver_sql(
            """
            SELECT
                before_code,
                before_name,
                base_category,
                after_code,
                after_name
            FROM upload_delivery_rule
            WHERE is_active = 1
            """
        ).mappings().all()

    rule_map = {}

    for rule in rules:
        before_code = rule["before_code"]
        base_categories = rule["base_category"] or "*"

        for category in base_categories.split(","):
            category = category.strip()

            if not category:
                continue

            rule_map[(before_code, category)] = dict(rule)

    converted_rows = []

    for row in rows:
        row = dict(row)

        delivery_code = row.get("delivery_code")
        product_code = row.get("product_code")
        base_category = product_base_map.get(product_code, "")

        row["base_category"] = base_category
        row["delivery_name_before_292"] = ""
        row["delivery_split_rule_292_applied"] = False

        rule = (
            rule_map.get((delivery_code, base_category))
            or rule_map.get((delivery_code, "*"))
        )

        if rule:
            row["delivery_name_before_292"] = row.get("delivery_name")
            row["delivery_code"] = rule["after_code"]
            row["delivery_name"] = rule["after_name"]
            row["delivery_split_rule_292_applied"] = True

        converted_rows.append(row)

    return converted_rows

# =========================
# 211 엑셀 업로드 자동변환
# =========================

def apply_dispatch_upload_rules(rows):
    rows = apply_product_name_rule_291_to_rows(rows)
    rows = apply_delivery_split_rule_292(rows)

    rows = add_applied_rule_labels(rows)
    rows = sort_applied_rules_first(rows)

    return rows    

def apply_delivery_split_rule_292(rows):
    product_codes = sorted({
        row.get("product_code")
        for row in rows
        if row.get("product_code")
    })

    product_base_map = {}

    with local_engine.connect() as conn:
        if product_codes:
            placeholders = ",".join(["?"] * len(product_codes))

            result = conn.exec_driver_sql(
                f"""
                SELECT code, base_category
                FROM product
                WHERE code IN ({placeholders})
                """,
                tuple(product_codes)
            )

            product_base_map = {
                row["code"]: row["base_category"]
                for row in result.mappings().all()
            }

        rules = conn.exec_driver_sql(
            """
            SELECT before_code, before_name, base_category, after_code, after_name
            FROM upload_delivery_rule
            WHERE is_active = 1
            """
        ).mappings().all()

    rule_map = {}

    for rule in rules:
        base_categories = rule["base_category"] or "*"

        for category in base_categories.split(","):
            category = category.strip()
            if category:
                rule_map[(rule["before_code"], category)] = dict(rule)

    converted_rows = []

    for row in rows:
        row = dict(row)

        delivery_code = row.get("delivery_code")
        product_code = row.get("product_code")
        base_category = product_base_map.get(product_code, "")

        row["base_category"] = base_category
        row["delivery_name_before_292"] = ""
        row["delivery_split_rule_292_applied"] = False
        row["delivery_split_rule_292_debug"] = f"{delivery_code} / {product_code} / {base_category}"

        rule = (
            rule_map.get((delivery_code, base_category))
            or rule_map.get((delivery_code, "*"))
        )

        if rule:
            row["delivery_name_before_292"] = row.get("delivery_name")
            row["delivery_code"] = rule["after_code"]
            row["delivery_name"] = rule["after_name"]
            row["delivery_split_rule_292_applied"] = True

        converted_rows.append(row)

    return converted_rows
