users = [
    ['Maxi', 'Rukavina'],
    ['Chris', 'Zeman'],
    ['Michi', 'Reinsperger'],
]

print(users)
for pair in users:
    if pair[0] == 'Chris':
        print(pair[1])

users = {
    'Maxi': 'Rukavina',
    'Chris': 'Zeman',
    'Michi': 'Reinsperger',
}

print(users['Chris'])