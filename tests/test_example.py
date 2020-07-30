import subprocess
import pytest
from .utils import is_probably_equal


TEST_CASES = [
    (
        "examples/quickstart.py",
        "Loaded grammar...\nI am a gorilla person.\nPeter is a gorilla person.\nTarzan is a love interest ofJane.\n",
    ),
    ("examples/readme.py", 'External execution!!!\nI am acting on span "[{\'orth\': \'head\', \'lemma\': \'head\', \'pos\': \'NOUN\'}, {\'orth\': \'hurts\', \'lemma\': \'hurt\', \'pos\': \'VERB\'}]" with data "[{\'callback\': \'mark_headache\', \'junk_attribute\': \'some string\', \'package\': \'headache\'}]".\nI am acting on span "[{\'orth\': \'head\', \'lemma\': \'head\', \'pos\': \'NOUN\'}, {\'orth\': \'hurts\', \'lemma\': \'hurt\', \'pos\': \'VERB\'}]" with data "{\'junk_attribute\': \'some string\', \'package\': \'headache\', \'callback\': \'mark_headache\'}".\n'),
]

@pytest.mark.parametrize(
    'src, expected',
    TEST_CASES
)
def test_end_to_end(src, expected):
    result = subprocess.run(
        ["python3", src], stdout=subprocess.PIPE, universal_newlines=True
    )
    assert is_probably_equal(result.stdout, expected)
