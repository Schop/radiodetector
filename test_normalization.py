"""Quick test of normalization function"""
from main import normalize_song_title

tests = [
    ('PHIL COLLINS', 'Phil Collins'),
    ("I CAN'T DANCE", "I Can't Dance"),
    ("I can't dance", "I Can't Dance"),
    ('two hearts', 'Two Hearts'),
    ('IN THE AIR TONIGHT', 'In The Air Tonight'),
    ("You Can't Hurry Love", "You Can't Hurry Love"),
]

print('Testing normalization:')
print('-' * 60)
all_pass = True
for original, expected in tests:
    result = normalize_song_title(original)
    status = '✓' if result == expected else '✗'
    print(f'{status} "{original:30}" -> "{result:30}"')
    if result != expected:
        print(f'  Expected: "{expected}"')
        all_pass = False

print('-' * 60)
if all_pass:
    print('✓ All tests passed!')
else:
    print('✗ Some tests failed')
