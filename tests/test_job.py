"""Job data model: uid dedup key and match_text scope."""
from jobbot.job import Job


def test_uid_stable_and_normalized():
    a = Job(title="Unity Developer", company="Acme", url="u1", source="s")
    b = Job(title="  unity   developer ", company="ACME", url="u2", source="s")
    # Same title+company (whitespace/case normalized) -> same uid despite different URL.
    assert a.uid == b.uid


def test_uid_distinct_titles_differ():
    a = Job(title="Unity Developer - Paper.io", company="Acme", url="", source="s")
    b = Job(title="Unity Developer - Growth", company="Acme", url="", source="s")
    assert a.uid != b.uid


def test_match_text_excludes_description():
    job = Job(title="Backend Engineer", company="Acme", url="", source="s",
              tags=["python"], description="we value unity here")
    text = job.match_text()
    assert "unity" not in text
    assert "backend engineer" in text
    assert "python" in text
