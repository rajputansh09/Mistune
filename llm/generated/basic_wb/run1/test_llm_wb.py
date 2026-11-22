import pytest
from mistune import helpers
from mistune.core import InlineState
from mistune.inline_parser import InlineParser


def tokens(src, **flags):
    p = InlineParser()
    st = InlineState({})
    st.src = src
    for k, v in flags.items():
        setattr(st, k, v)
    return p.render(st)


def test_llm_wb_01_unescape_char_plain_text_unchanged():
    assert helpers.unescape_char("abc") == "abc"


def test_llm_wb_02_unescape_char_single_backslash_before_char():
    assert helpers.unescape_char(r"\*") == "*"


def test_llm_wb_03_unescape_char_multiple_escapes():
    assert helpers.unescape_char(r"\[\]") == "[]"


def test_llm_wb_04_parse_link_text_simple_brackets():
    assert helpers.parse_link_text("[abc]", 1) == ("abc", 5)


def test_llm_wb_05_parse_link_text_nested_brackets():
    assert helpers.parse_link_text("[a[b]c]", 1) == ("a[b]c", 7)


def test_llm_wb_06_parse_link_text_unclosed_returns_none():
    assert helpers.parse_link_text("[abc", 1) == (None, None)


def test_llm_wb_07_parse_link_text_start_at_non_bracket_position():
    assert helpers.parse_link_text("x[abc]", 2) == ("abc", 6)


def test_llm_wb_08_parse_link_text_multiple_nested_levels():
    assert helpers.parse_link_text("[a[b[c]d]e]", 1) == ("a[b[c]d]e", 11)


def test_llm_wb_09_parse_link_label_simple():
    assert helpers.parse_link_label("[label]:", 0) == ("label", 8)


def test_llm_wb_10_parse_link_label_with_spaces():
    assert helpers.parse_link_label("[A B C]:", 0) == ("A B C", 8)


def test_llm_wb_11_parse_link_label_invalid_missing_colon():
    assert helpers.parse_link_label("[label]", 0) == (None, None)


def test_llm_wb_12_parse_link_label_invalid_empty_label():
    assert helpers.parse_link_label("[]:", 0) == (None, None)


def test_llm_wb_13_parse_link_href_inline_angle_brackets():
    assert helpers.parse_link_href("<https://example.com>", 0) == ("https://example.com", 21)


def test_llm_wb_14_parse_link_href_inline_raw_url():
    assert helpers.parse_link_href("https://example.com)", 0) == ("https://example.com", 19)


def test_llm_wb_15_parse_link_href_block_raw_url():
    assert helpers.parse_link_href("https://example.com)", 0, block=True) == ("https://example.com", 19)


def test_llm_wb_16_parse_link_href_block_matches_closing_delimiter():
    assert helpers.parse_link_href("https://example.com>", 0, block=True) == ("https://example.com", 20)


def test_llm_wb_17_parse_link_href_invalid_start():
    assert helpers.parse_link_href("xhttps://example.com", 0) == (None, None)


def test_llm_wb_18_parse_link_href_empty_angle_brackets():
    assert helpers.parse_link_href("<>", 0) == ("", 2)


def test_llm_wb_19_parse_link_title_double_quoted():
    assert helpers.parse_link_title('"hello"', 0, 7) == ("hello", 7)


def test_llm_wb_20_parse_link_title_single_quoted_with_escape():
    assert helpers.parse_link_title("'a\\\"b'", 0, 6) == ('a"b', 6)


def test_llm_wb_21_parse_link_title_parenthesized():
    assert helpers.parse_link_title("(abc)", 0, 5) == ("abc", 5)


def test_llm_wb_22_parse_link_title_invalid_no_quotes_or_parens():
    assert helpers.parse_link_title("hello", 0, 5) == (None, None)


def test_llm_wb_23_parse_link_title_respects_max_pos():
    assert helpers.parse_link_title('"hello"', 0, 6) == (None, None)


def test_llm_wb_24_parse_link_simple_inline_link():
    assert helpers.parse_link("(https://example.com)", 1) == (
        {"url": "https://example.com"},
        21,
    )


def test_llm_wb_25_parse_link_with_title():
    assert helpers.parse_link('(https://example.com "hi")', 1) == (
        {"url": "https://example.com", "title": "hi"},
        26,
    )


def test_llm_wb_26_parse_link_with_escaped_url_characters():
    assert helpers.parse_link(r"(https://example.com/a\)b)", 1) == (
        {"url": "https://example.com/a)b"},
        26,
    )


def test_llm_wb_27_parse_link_invalid_missing_paren_end():
    assert helpers.parse_link("(https://example.com", 1) == (None, None)


def test_llm_wb_28_parse_link_invalid_bad_href():
    assert helpers.parse_link("([broken])", 1) == (None, None)


def test_llm_wb_29_parse_link_invalid_bad_title():
    assert helpers.parse_link('(https://example.com "unterminated)', 1) == (None, None)


def test_llm_wb_30_codespan_simple_one_backtick():
    assert tokens("`code`") == [{"type": "codespan", "raw": "code"}]


def test_llm_wb_31_codespan_trim_outer_spaces():
    assert tokens("` code `") == [{"type": "codespan", "raw": "code"}]


def test_llm_wb_32_codespan_preserve_internal_spaces():
    assert tokens("`a  b`") == [{"type": "codespan", "raw": "a  b"}]


def test_llm_wb_33_codespan_newlines_become_spaces():
    assert tokens("`a\nb`") == [{"type": "codespan", "raw": "a b"}]


def test_llm_wb_34_codespan_empty_content_becomes_text_when_no_match():
    assert tokens("``") == [{"type": "text", "raw": "``"}]


def test_llm_wb_35_codespan_marker_mismatch_falls_back_to_text():
    assert tokens("`code``") == [{"type": "text", "raw": "`"}]


def test_llm_wb_36_codespan_double_backtick_matching():
    assert tokens("``code``") == [{"type": "codespan", "raw": "code"}]


def test_llm_wb_37_emphasis_simple_emphasis():
    assert tokens("*a*") == [{"type": "emphasis", "children": [{"type": "text", "raw": "a"}]}]


def test_llm_wb_38_emphasis_simple_strong():
    assert tokens("**a**") == [{"type": "strong", "children": [{"type": "text", "raw": "a"}]}]


def test_llm_wb_39_emphasis_nested_emphasis_within_strong():
    assert tokens("**a *b* c**") == [
        {
            "type": "strong",
            "children": [
                {"type": "text", "raw": "a "},
                {"type": "emphasis", "children": [{"type": "text", "raw": "b"}]},
                {"type": "text", "raw": " c"},
            ],
        }
    ]


def test_llm_wb_40_emphasis_in_emphasis_flag_prevents_recursive_parse():
    assert tokens("*a*", in_emphasis=True) == [{"type": "text", "raw": "*"}]
