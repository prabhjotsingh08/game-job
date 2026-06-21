"""Filter logic: keyword include/exclude (whole-word) and remote detection."""
from jobbot.config import Config
from jobbot.filters import is_remote, matches
from jobbot.job import Job


def _cfg(**over):
    data = {
        "keywords": ["unity", "unity3d", "unity developer"],
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


def test_description_is_ignored_for_matching():
    # Strict title-only: Unity in the body must NOT pull in a non-Unity title, any source.
    hn = Job(title="hiring", company="x", url="", source="HackerNews",
             description="We use Unity for our game, hiring a developer.")
    other = Job(title="hiring", company="x", url="", source="RemoteOK",
                description="We use Unity for our game.")
    assert not matches(hn, _cfg())
    assert not matches(other, _cfg())


def test_tags_are_ignored_for_matching():
    # A "unity" tag must not pull in a non-Unity title.
    job = Job(title="Data Scientist", company="x", url="", source="RemoteOK",
              tags=["unity", "databricks"])
    assert not matches(job, _cfg())


def test_studio_unity_only_in_description_does_not_match():
    # Title doesn't name Unity (only the JD does) -> strict rule drops it.
    job = Job(title="Gameplay Programmer", company="riotgames", url="",
              source="Greenhouse/riotgames", description="You'll build in Unity all day.")
    assert not matches(job, _cfg())


def test_studio_unity_developer_title_matches():
    # A studio role whose TITLE names Unity + a dev term is kept.
    job = Job(title="Unity Developer", company="acme", url="", source="Lever/acme",
              description="You'll report to the Principal Engineer.")
    assert matches(job, _cfg(keywords=["unity"], exclude=["principal"]))


def test_unity_non_dev_role_dropped():
    # "Unity" present but the role is not a developer/engineer role -> dropped.
    for t in ("Unity Artist", "Unity Technical Designer", "Unity Community Manager"):
        job = Job(title=t, company="x", url="", source="RemoteOK")
        assert not matches(job, _cfg()), t


def test_dev_role_without_unity_dropped():
    job = Job(title="Software Engineer", company="x", url="", source="RemoteOK")
    assert not matches(job, _cfg())


def test_unity_engineer_and_unity3d_programmer_match():
    for t in ("Senior Unity Engineer", "Unity3D Programmer", "Remote Unity Developer"):
        job = Job(title=t, company="x", url="", source="RemoteOK")
        assert matches(job, _cfg()), t


def test_prefiltered_source_needs_only_dev_role():
    # Adzuna/Jooble are queried "unity developer" -> title needs only a dev term, not "unity".
    ad = Job(title="Game Developer", company="x", url="", source="Adzuna")
    assert matches(ad, _cfg())
    # Same title from a generic source still requires "unity" in the title -> dropped.
    ok = Job(title="Game Developer", company="x", url="", source="RemoteOK")
    assert not matches(ok, _cfg())


def test_prefiltered_source_still_needs_dev_role_and_exclude():
    # A non-dev role from a prefiltered source is still dropped.
    artist = Job(title="Concept Artist", company="x", url="", source="Adzuna")
    assert not matches(artist, _cfg())


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
