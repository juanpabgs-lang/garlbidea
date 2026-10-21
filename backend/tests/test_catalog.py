from garleb_desk.catalog import country_by_any, iso2, m49, product_by_any, resolve_region


def test_country_aliases():
    assert country_by_any("turkey").iso2 == "TR"
    assert country_by_any("UAE").iso2 == "AE"
    assert country_by_any("kenya").iso2 == "KE"
    assert iso2("792") == "TR"
    assert m49("IT") == 380


def test_regions():
    assert "AE" in resolve_region("gulf")
    assert "KE" in resolve_region("east africa")


def test_products():
    assert product_by_any("pasta").code == "1902"
    assert product_by_any("semolina").code == "110311"
