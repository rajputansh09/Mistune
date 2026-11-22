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


def test_llm_wb_01_unescape_char_replaces_escape():
    assert helpers.unescape_char(r"a\*b") == "a*b"


def test_llm_wb_02_unescape_char_leaves_plain_text():
    assert helpers.unescape_char("abc") == "abc"


def test_llm_wb_03_unescape_char_multiple_escapes():
    assert helpers.unescape_char(r"\*\_\[") == "*_["


def test_llm_wb_04_parse_link_text_simple():
    assert helpers.parse_link_text("[abc]", 1) == ("abc", 5)


def test_llm_wb_05_parse_link_text_nested_brackets():
    assert helpers.parse_link_text("[a[b]c]", 1) == ("a[b]c", 7)


def test_llm_wb_06_parse_link_text_no_closing_bracket():
    assert helpers.parse_link_text("[abc", 1) == (None, None)


def test_llm_wb_07_parse_link_text_start_after_nested_open():
    assert helpers.parse_link_text("x[a[b]c]y", 2) == ("a[b]c", 8)


def test_llm_wb_08_parse_link_label_simple():
    assert helpers.parse_link_label("[label]:", 0) == ("label", 8)


def test_llm_wb_09_parse_link_label_with_spaces_inside():
    assert helpers.parse_link_label("[a b c]:", 0) == ("a b c", 8)


def test_llm_wb_10_parse_link_label_invalid_missing_colon():
    assert helpers.parse_link_label("[label]", 0) == (None, None)


def test_llm_wb_11_parse_link_href_inline_basic():
    assert helpers.parse_link_href("(http://a.com)", 0) == ("http://a.com", 13)


def test_llm_wb_12_parse_link_href_inline_with_angle_brackets():
    assert helpers.parse_link_href("(<http://a.com>)", 0) == ("http://a.com", 15)


def test_llm_wb_13_parse_link_href_block_basic():
    assert helpers.parse_link_href("(http://a.com)\n", 0, block=True) == ("http://a.com", 13)


def test_llm_wb_14_parse_link_href_block_trailing_paren_kept_in_href_when_matching():
    assert helpers.parse_link_href("(http://a.com))", 0, block=True) == ("http://a.com)", 15)


def test_llm_wb_15_parse_link_href_invalid():
    assert helpers.parse_link_href("abc", 0) == (None, None)


def test_llm_wb_16_parse_link_title_double_quotes():
    assert helpers.parse_link_title(' "title"', 0, 8) == ("title", 8)


def test_llm_wb_17_parse_link_title_single_quotes():
    assert helpers.parse_link_title(" 'title'", 0, 8) == ("title", 8)


def test_llm_wb_18_parse_link_title_parentheses():
    assert helpers.parse_link_title(" (title)", 0, 8) == ("title", 8)


def test_llm_wb_19_parse_link_title_unescapes_escaped_chars():
    assert helpers.parse_link_title(r' "a\*b"', 0, 7) == ("a*b", 7)


def test_llm_wb_20_parse_link_title_invalid():
    assert helpers.parse_link_title(" title", 0, 6) == (None, None)


def test_llm_wb_21_parse_link_simple_no_title():
    attrs, end = helpers.parse_link("(http://a.com)", 0)
    assert attrs == {"url": "http://a.com"}
    assert end == 14


def test_llm_wb_22_parse_link_simple_with_title():
    attrs, end = helpers.parse_link('(http://a.com "x")', 0)
    assert attrs == {"url": "http://a.com", "title": "x"}
    assert end == 18


def test_llm_wb_23_parse_link_with_escaped_url_chars():
    attrs, end = helpers.parse_link(r'(http://a.com/a\)b)', 0)
    assert attrs == {"url": "http://a.com/a)b"}
    assert end == 19


def test_llm_wb_24_parse_link_invalid_missing_paren():
    assert helpers.parse_link("(http://a.com", 0) == (None, None)


def test_llm_wb_25_tokens_codespan_basic():
    assert tokens("`code`") == [{"type": "codespan", "raw": "code"}]


def test_llm_wb_26_tokens_codespan_trims_surrounding_spaces():
    assert tokens("` code `") == [{"type": "codespan", "raw": "code"}]


def test_llm_wb_27_tokens_codespan_preserves_internal_spaces():
    assert tokens("`a  b`") == [{"type": "codespan", "raw": "a  b"}]


def test_llm_wb_28_tokens_codespan_newline_becomes_space():
    assert tokens("`a\nb`") == [{"type": "codespan", "raw": "a b"}]


def test_llm_wb_29_tokens_codespan_multiple_backticks():
    assert tokens("``code``") == [{"type": "codespan", "raw": "code"}]


def test_llm_wb_30_tokens_codespan_fallback_to_text_when_no_end():
    assert tokens("`code") == [{"type": "text", "raw": "`"}]


def test_llm_wb_31_tokens_emphasis_basic():
    assert tokens("*em*") == [{"type": "emphasis", "children": [{"type": "text", "raw": "em"}]}]


def test_llm_wb_32_tokens_strong_basic():
    assert tokens("**strong**") == [{"type": "strong", "children": [{"type": "text", "raw": "strong"}]}]


def test_llm_wb_33_tokens_triple_marker_nested_strong_in_emphasis():
    assert tokens("***x***") == [
        {
            "type": "emphasis",
            "children": [
                {"type": "strong", "children": [{"type": "text", "raw": "x"}]}
            ],
        }
    ]


def test_llm_wb_34_tokens_emphasis_in_strong():
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


def test_llm_wb_35_tokens_literal_star_inside_emphasis_when_already_in_emphasis():
    assert tokens("a*b*c", in_emphasis=True) == [
        {"type": "text", "raw": "a"},
        {"type": "text", "raw": "*"},
        {"type": "text", "raw": "b"},
        {"type": "text", "raw": "*"},
        {"type": "text", "raw": "c"},
    ]


def test_llm_wb_36_tokens_literal_double_star_inside_strong_when_already_in_strong():
    assert tokens("a**b**c", in_strong=True) == [
        {"type": "text", "raw": "a"},
        {"type": "text", "raw": "**"},
        {"type": "text", "raw": "b"},
        {"type": "text", "raw": "**"},
        {"type": "text", "raw": "c"},
    ]


def test_llm_wb_37_tokens_unmatched_emphasis_marker_becomes_text():
    assert tokens("*abc") == [{"type": "text", "raw": "*"}]


def test_llm_wb_38_tokens_unmatched_strong_marker_becomes_text():
    assert tokens("**abc") == [{"type": "text", "raw": "**"}]


def test_llm_wb_39_tokens_codespan_with_backticks_in_content():
    assert tokens("`a``b`") == [{"type": "codespan", "raw": "a``b"}]


def test_llm_wb_40_tokens_emphasis_and_text_tail():
    assert tokens("*a* b") == [
        {"type": "emphasis", "children": [{"type": "text", "raw": "a"}]},
        {"type": "text", "raw": " "},
        {"type": "text", "raw": "b"},
    ]
