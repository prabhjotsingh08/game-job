"""Filter logic: keyword include/exclude (whole-word) and remote detection."""
from jobbot.config import Config
from jobbot.filters import is_remote, matches
from jobbot.job import Job


def _cfg(**over):
    data = {
        "keywords": ["unity", "unity developer"],
        "exclude": ["principal", "unity catalog"],
    }
    data.update(over)
    return Config(data)


def test_matches_keyword_hit():
    job = Job(title="Unity Developer", company="Acme", url="", source="RemoteOK")
    assert matches(job, _cfg())


def test_matches_word_boundary_no_substring():
    # "unity" inside "community" must NOT match.
    job = Job(title="Community Manager", company="Acme", url="", source="RemoteOK")
    assert not matches(job, _cfg())


def test_exclude_drops_even_on_keyword_hit():
    job = Job(title="Principal Unity Engineer", company="Acme", url="", source="RemoteOK")
    assert not matches(job, _cfg(keywords=["unity"], exclude=["principal"]))


def test_unity_catalog_excluded():
    # Databricks false positive killed by the "unity catalog" exclude term.
    job = Job(
        title="Data Engineer (Unity Catalog)", company="DB", url="", source="RemoteOK"
    )
    assert not matches(job, _cfg())


def test_body_match_source_uses_description():
    # HackerNews matches against the body; non-body source with same data does not.
    hn = Job(title="hiring", company="x", url="", source="HackerNews",
             description="We use Unity for our game.")
    other = Job(title="hiring", company="x", url="", source="RemoteOK",
                description="We use Unity for our game.")
    assert matches(hn, _cfg())
    assert not matches(other, _cfg())


def test_title_only_source_ignores_tags():
    # Remotive matches title only; a "unity" tag must not pull in a non-Unity title.
    job = Job(title="Data Scientist", company="x", url="", source="Remotive",
              tags=["unity", "databricks"])
    assert not matches(job, _cfg())


def test_studio_matches_unity_in_description_only():
    # Title doesn't name Unity, but the JD does -> studio body scan should match.
    job = Job(title="Gameplay Programmer", company="riotgames", url="",
              source="Greenhouse/riotgames", description="You'll build in Unity all day.")
    assert matches(job, _cfg())


def test_studio_exclude_stays_narrow_ignores_jd_boilerplate():
    # "principal" appears only in JD boilerplate; studio exclude scans title+tags only,
    # so a real Unity role is NOT dropped.
    job = Job(title="Unity Developer", company="acme", url="", source="Lever/acme",
              description="You'll report to the Principal Engineer.")
    assert matches(job, _cfg(keywords=["unity"], exclude=["principal"]))


def test_studio_remote_from_description():
    # Onsite-looking title/location, but JD says remote -> is_remote True for studios.
    job = Job(title="Unity Developer", company="acme", url="", source="Ashby/acme",
              location="London", description="This role is fully remote.")
    assert is_remote(job)


def test_remote_only_source_always_remote():
    job = Job(title="Unity Dev", company="x", url="", source="RemoteOK", location="USA")
    assert is_remote(job)


def test_remote_term_word_boundary():
    # "global" as a whole word -> remote; inside "globalization" -> not.
    yes = Job(title="Unity Dev", company="x", url="", source="Greenhouse/acme",
              location="Global")
    no = Job(title="Globalization Lead", company="x", url="", source="Greenhouse/acme",
             location="New York")
    assert is_remote(yes)
    assert not is_remote(no)
