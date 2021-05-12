import nox
from nox.sessions import Session

nox.options.sessions = "lint", "mypy", "tests"
locations = "hmrb", "docs/conf.py"


@nox.session(python=["3.7"])
def requirements(session: Session) -> None:
    args = session.posargs or ["-o", "requirements.txt", "requirements.in"]
    session.install("pip-tools")
    session.run("pip-compile", *args)


@nox.session(python=["3.7"])
def black(session: Session) -> None:
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)


@nox.session(python=["3.7"])
def lint(session: Session) -> None:
    args = session.posargs or locations
    session.install(
        "flake8",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-import-order",
    )
    session.run("flake8", *args)


@nox.session(python=["3.7"])
def types(session: Session) -> None:
    args = session.posargs or locations
    session.install("mypy")
    session.run("mypy", *args)


@nox.session(python=["3.7"])
def safety(session: Session) -> None:
    session.install("safety")
    session.run("safety", "check", "--file=requirements.txt", "--full-report")


@nox.session(python=["3.6", "3.7", "3.8", "3.9"])
def tests(session: Session) -> None:
    session.install("pytest", "pytest-cov")
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests",
        "--cov-config",
        ".coveragerc",
        "--cov",
        ".",
        env={"PYTHONHASHSEED": "42"},
    )
    session.run("coverage", "xml")


@nox.session(python=["3.9"])
def test_spacy2(session: Session) -> None:
    session.install("pytest")
    session.install("spacy<3.0.0")
    session.run("spacy", "download", "en_core_web_sm")
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests/test_spacy.py",
        )


@nox.session(python=["3.9"])
def test_spacy3(session: Session) -> None:
    session.install("pytest")
    session.install("spacy>=3.0.0")
    session.run("spacy", "download", "en_core_web_sm")
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests/test_spacy.py",
        )


@nox.session(python=["3.7"])
def changelog(session: Session) -> None:
    args = session.posargs or ["--unreleased"]
    session.install("auto-changelog")
    session.run("auto-changelog", *args)


@nox.session(python=["3.7"])
def docs(session: Session) -> None:
    args = session.posargs or locations
    session.install("-r", "doc_requirements.txt")
    session.install("-r", "requirements.txt")
    session.install("-e", ".")
    session.install("sphinx-autobuild")
    session.install(".")
    session.run(*args)


@nox.session(python=["3.7"])
def publish(session: Session) -> None:
    args = session.posargs or ["-r","testpypi"]
    args += ["dist/*"]
    session.install("twine", "wheel", "setuptools")
    session.run("rm", "-rf", "dist", "build", external=True)
    session.run("python", "setup.py", "--quiet", "sdist", "bdist_wheel")
    session.run("twine", "check", "--strict", "dist/*")
    session.run("twine","upload", *args)
