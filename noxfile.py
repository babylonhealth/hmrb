import nox
from nox.sessions import Session

nox.options.sessions = "lint", "mypy", "tests"
locations = "hmrb", "noxfile.py", "docs/conf.py"


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


@nox.session(python=["3.6", "3.7", "3.8"])
def tests_v1(session: Session) -> None:
    session.install("pytest", "pytest-cov")
    session.run("pip", "install", "-r", "requirements.txt")
    session.run("pip", "install", "-e", ".")
    session.run(
        "pytest",
        "hmrb/compat",
        "--cov-config",
        ".coveragerc",
        "--cov",
        ".",
        env={"PYTHONHASHSEED": "42"},
    )
    session.run("coverage", "xml")


@nox.session(python=["3.6", "3.7", "3.8"])
def tests_v2(session: Session) -> None:
    session.install("pytest", "pytest-cov")
    session.run("pip", "install", "-r", "requirements.txt")
    session.run("pip", "install", "-e", ".")
    session.run("pytest", "hmrb/tests", "--cov-config=.coveragerc", "--cov")
    session.chdir("hmrb/rust")
    session.run("cargo", "test")



@nox.session(python=["3.7"])
def changelog(session: Session) -> None:
    args = session.posargs or ["--unreleased"]
    session.install("auto-changelog")
    session.run("auto-changelog", *args)
