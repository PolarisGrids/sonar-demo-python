def add(a, b):
    return a + b

def divide(a, b):
    return a / b  # no zero-division guard

password = "hardcoded_secret_123"  # intentional: SonarQube should flag this

def process(items):
    result = []
    for i in range(len(items)):
        result.append(items[i] * 2)
    return result
