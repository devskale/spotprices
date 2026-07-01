# tests/test_tarifliste_parser.py
"""Pure-function tests for the tariff markdown parser and the brutto->netto
normalizer in electricity/api/v1/endpoints/tarifliste.py.

These tests do no I/O and no network — they exercise the parsing logic
directly with fixture strings.
"""

from electricity.api.v1.endpoints.tarifliste import (
    normalize_strompreis_to_netto_exkl_mwst,
    parse_markdown_table,
)
from electricity.api.v1.models import TarifInfo


# --- normalize_strompreis_to_netto_exkl_mwst -------------------------------

class TestNormalizeNetto:
    def test_brutto_is_converted_to_netto(self):
        # 24 ct/kWh brutto -> 24/1.2 = 20 ct/kWh netto
        assert normalize_strompreis_to_netto_exkl_mwst("24,00 ct/kWh (brutto)") == "20,0000 ct/kWh"

    def test_brutto_with_dot_decimal(self):
        assert normalize_strompreis_to_netto_exkl_mwst("24.00 ct/kWh (brutto)") == "20,0000 ct/kWh"

    def test_case_insensitive_brutto(self):
        assert normalize_strompreis_to_netto_exkl_mwst("24,00 CT/KWH (BRUTTO)") == "20,0000 ct/kWh"

    def test_netto_left_untouched(self):
        # Values without (brutto) must pass through unchanged.
        assert normalize_strompreis_to_netto_exkl_mwst("20,00 ct/kWh netto") == "20,00 ct/kWh netto"

    def test_plain_value_left_untouched(self):
        assert normalize_strompreis_to_netto_exkl_mwst("14,55 ct/kWh") == "14,55 ct/kWh"

    def test_dynamic_formula_left_untouched(self):
        assert normalize_strompreis_to_netto_exkl_mwst("EPEX Spot AT + 1,44 ct/kWh") == "EPEX Spot AT + 1,44 ct/kWh"

    def test_multiple_brutto_in_string(self):
        result = normalize_strompreis_to_netto_exkl_mwst(
            "14,40 ct/kWh (brutto); 12,00 ct/kWh (brutto)")
        assert "12,0000 ct/kWh" in result
        assert "10,0000 ct/kWh" in result

    def test_empty_string(self):
        assert normalize_strompreis_to_netto_exkl_mwst("") == ""

    def test_invalid_number_left_untouched(self):
        # If the number can't be parsed, the original match is kept.
        assert normalize_strompreis_to_netto_exkl_mwst("abc ct/kWh (brutto)") == "abc ct/kWh (brutto)"


# --- parse_markdown_table -------------------------------------------------

# A representative report table matching the TARIF_TABELLE query schema.
SAMPLE_TABLE = """| Stromanbieter | Tarifname | Tarifart | Preisanpassung | Strompreis (ct/kWh netto) | Link | Kurzbeschreibung |
|:--------------|:----------|:---------|:---------------|:-------------------------|:----|:----------------|
| WienEnergie | Strom Fix 24 | Bezug | Fixpreis | 24,50 ct/kWh | https://wienenergie.at | Fixpreis 24 Monate |
| Verbund | OPTIMA Entspannt | Bezug | Fixpreis | 26,90 ct/kWh | https://verbund.com | Fixpreis 12 Monate |
| OEMAG | Marktpreis | Einspeisung | Monatlich | 9,10 ct/kWh | https://oem-ag.at | Stand Jan 2026 |
"""


class TestParseMarkdownTable:
    def test_parses_all_rows(self):
        tarife = parse_markdown_table(SAMPLE_TABLE)
        assert len(tarife) == 3

    def test_extracts_fields(self):
        tarife = parse_markdown_table(SAMPLE_TABLE)
        t = tarife[0]
        assert t.stromanbieter == "WienEnergie"
        assert t.tarifname == "Strom Fix 24"
        assert t.tarifart == "Bezug"
        assert t.preisanpassung == "Fixpreis"
        assert t.strompreis == "24,50 ct/kWh"
        assert t.link == "https://wienenergie.at"
        assert t.kurzbeschreibung == "Fixpreis 24 Monate"

    def test_returns_tarifinfo_objects(self):
        tarife = parse_markdown_table(SAMPLE_TABLE)
        assert all(isinstance(t, TarifInfo) for t in tarife)

    def test_normalizes_brutto_in_strompreis(self):
        table = """| Stromanbieter | Tarifname | Tarifart | Preisanpassung | Strompreis (ct/kWh netto) | Link | Kurzbeschreibung |
|:---|:---|:---|:---|:---|:---|:---|
| Test | Tarif | Bezug | Fix | 24,00 ct/kWh (brutto) | - | test |"""
        tarife = parse_markdown_table(table)
        assert tarife[0].strompreis == "20,0000 ct/kWh"

    def test_skips_header_and_separator(self):
        tarife = parse_markdown_table(SAMPLE_TABLE)
        # First data row is WienEnergie, not "Stromanbieter"
        assert tarife[0].stromanbieter == "WienEnergie"

    def test_tolerates_leading_text_before_table(self):
        # The LLM sometimes emits a think block before the table.
        content = "Some preamble text.\n\n" + SAMPLE_TABLE
        tarife = parse_markdown_table(content)
        assert len(tarife) == 3

    def test_empty_table_returns_empty_list(self):
        assert parse_markdown_table("") == []

    def test_table_with_only_header_returns_empty(self):
        header_only = """| Stromanbieter | Tarifname | Tarifart | Preisanpassung | Strompreis (ct/kWh netto) | Link | Kurzbeschreibung |
|:---|:---|:---|:---|:---|:---|:---|"""
        assert parse_markdown_table(header_only) == []

    def test_six_column_row_uses_default_link(self):
        # Rows with 6 columns (no link) should still parse with link="-"
        table = """| Stromanbieter | Tarifname | Tarifart | Preisanpassung | Strompreis (ct/kWh netto) | Kurzbeschreibung |
|:---|:---|:---|:---|:---|:---|
| Test | Tarif | Bezug | Fix | 25,00 ct/kWh | test |"""
        tarife = parse_markdown_table(table)
        assert len(tarife) == 1
        assert tarife[0].kurzbeschreibung == "test"
