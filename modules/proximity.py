from typing import List


def proximity(first, second):
    first = first.lower().strip()
    second = second.lower().strip()
    first_set = set()
    second_set = set()

    for j in range(0, len(first)):
        for i in range(len(first) - j):
            first_set.add(first[i:i + 1 + j])

    for j in range(0, len(second)):
        for i in range(len(second) - j):
            second_set.add(second[i:i + 1 + j])

    return len(first_set & second_set) / len(first_set | second_set)


def find_field(sample_field: str, layer_fields: List) -> str:
    proximity_list = [proximity(sample_field, field) for field in layer_fields]
    return layer_fields[proximity_list.index(max(proximity_list))]
