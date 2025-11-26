#!/usr/bin/env python3
"""
Script to download animal images for the similarity search dataset
"""
import os
import requests
import uuid
from pathlib import Path
import time

# All image URLs organized by category
ANIMAL_IMAGES = {
    # BIRDS (from first batch)
    "eagle": [
        "https://images.unsplash.com/photo-1531884070720-875c7622d4c6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwxfHxlYWdsZXxlbnwwfHx8fDE3NjQxNTcxNjF8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1557401622-cfc0aa5d146c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwyfHxlYWdsZXxlbnwwfHx8fDE3NjQxNTcxNjF8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "owl": [
        "https://images.unsplash.com/photo-1553264701-d138db4fd5d4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxvd2x8ZW58MHx8fHwxNzY0MTU3MTY4fDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1628126907372-761f54441c1b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHw0fHxvd2x8ZW58MHx8fHwxNzY0MTU3MTY4fDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "parrot": [
        "https://images.unsplash.com/photo-1552728089-57bdde30beb3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwxfHxwYXJyb3R8ZW58MHx8fHwxNzY0MTU3MTczfDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1452570053594-1b985d6ea890?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwzfHxwYXJyb3R8ZW58MHx8fHwxNzY0MTU3MTczfDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "penguin": [
        "https://images.unsplash.com/photo-1598439210625-5067c578f3f6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHxwZW5ndWlufGVufDB8fHx8MTc2NDE1NzE3OHww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1551986782-d0169b3f8fa7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHw0fHxwZW5ndWlufGVufDB8fHx8MTc2NDE1NzE3OHww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "flamingo": [
        "https://images.unsplash.com/photo-1629394661462-13ea8fe156ef?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwyfHxmbGFtaW5nb3xlbnwwfHx8fDE3NjQxNTcxODJ8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1497206365907-f5e630693df0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwzfHxmbGFtaW5nb3xlbnwwfHx8fDE3NjQxNTcxODJ8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "peacock": [
        "https://images.unsplash.com/photo-1536514900905-0d5511b9d489?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxwZWFjb2NrfGVufDB8fHx8MTc2NDE1NzM4Mnww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1587011158961-5f27e4578293?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHw0fHxwZWFjb2NrfGVufDB8fHx8MTc2NDE1NzM4Mnww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    
    # SEA CREATURES
    "shark": [
        "https://images.unsplash.com/photo-1560275619-4662e36fa65c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxzaGFya3xlbnwwfHx8fDE3NjQxNTcxODd8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1531959870249-9f9b729efcf4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwyfHxzaGFya3xlbnwwfHx8fDE3NjQxNTcxODd8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "dolphin": [
        "https://images.unsplash.com/photo-1570481662006-a3a1374699e8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwxfHxkb2xwaGlufGVufDB8fHx8MTc2NDE1NzE5M3ww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1547382442-d17c21625a44?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1NzZ8MHwxfHNlYXJjaHwyfHxkb2xwaGlufGVufDB8fHx8MTc2NDE1NzE5M3ww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "whale": [
        "https://images.unsplash.com/photo-1568430462989-44163eb1752f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxfHx3aGFsZXxlbnwwfHx8fDE3NjQxNTcxOTl8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1698472505070-6d3b90afb530?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwyfHx3aGFsZXxlbnwwfHx8fDE3NjQxNTcxOTl8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "octopus": [
        "https://images.unsplash.com/photo-1628944681206-2ee8d63b0a6b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwxfHxvY3RvcHVzfGVufDB8fHx8MTc2NDE1NzIwNHww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1523486230352-65ff5222cea4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwzfHxvY3RvcHVzfGVufDB8fHx8MTc2NDE1NzIwNHww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "turtle": [
        "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxzZWElMjB0dXJ0bGV8ZW58MHx8fHwxNzY0MTU3MjA5fDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1573551089778-46a7abc39d9f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwzfHxzZWElMjB0dXJ0bGV8ZW58MHx8fHwxNzY0MTU3MjA5fDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "goldfish": [
        "https://images.unsplash.com/photo-1522069169874-c58ec4b76be5?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHxnb2xkZmlzaHxlbnwwfHx8fDE3NjQxNTczNjF8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1625369708811-65ebfc5ca632?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwyfHxnb2xkZmlzaHxlbnwwfHx8fDE3NjQxNTczNjF8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "clownfish": [
        "https://images.unsplash.com/photo-1535591273668-578e31182c4f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHxjbG93bmZpc2h8ZW58MHx8fHwxNzY0MTU3MzY2fDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1544552866-d3ed42536cfd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwyfHxjbG93bmZpc2h8ZW58MHx8fHwxNzY0MTU3MzY2fDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    
    # WILDLIFE
    "bear": [
        "https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxiZWFyfGVufDB8fHx8MTc2NDE1NzIxNXww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1568162603664-fcd658421851?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwzfHxiZWFyfGVufDB8fHx8MTc2NDE1NzIxNXww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "wolf": [
        "https://images.unsplash.com/photo-1588167056547-c183313da47c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHx3b2xmfGVufDB8fHx8MTc2NDE1NzIyMXww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1590420485404-f86d22b8abf8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwyfHx3b2xmfGVufDB8fHx8MTc2NDE1NzIyMXww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "deer": [
        "https://images.unsplash.com/photo-1484406566174-9da000fda645?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxkZWVyfGVufDB8fHx8MTc2NDE1NzIyN3ww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1543946207-39bd91e70ca7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwzfHxkZWVyfGVufDB8fHx8MTc2NDE1NzIyN3ww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "zebra": [
        "https://images.unsplash.com/photo-1526319238109-524eecb9b913?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwxfHx6ZWJyYXxlbnwwfHx8fDE3NjQxNTcyMzN8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1574451966652-62debbb4c221?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwzfHx6ZWJyYXxlbnwwfHx8fDE3NjQxNTcyMzN8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "giraffe": [
        "https://images.unsplash.com/photo-1534567110243-8875d64ca8ff?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwxfHxnaXJhZmZlfGVufDB8fHx8MTc2NDEwNDQ4OHww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1547721064-da6cfb341d50?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwzfHxnaXJhZmZlfGVufDB8fHx8MTc2NDEwNDQ4OHww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "fox": [
        "https://images.unsplash.com/photo-1644125003076-ce465d331769?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwxfHxmb3h8ZW58MHx8fHwxNzY0MTU3Mzc3fDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1516934024742-b461fba47600?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDJ8MHwxfHNlYXJjaHwzfHxmb3h8ZW58MHx8fHwxNzY0MTU3Mzc3fDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "rabbit": [
        "https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwxfHxyYWJiaXR8ZW58MHx8fHwxNzY0MTM2Mjk4fDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1535241749838-299277b6305f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwzfHxyYWJiaXR8ZW58MHx8fHwxNzY0MTM2Mjk4fDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "panda": [
        "https://images.unsplash.com/photo-1527118732049-c88155f2107c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxwYW5kYXxlbnwwfHx8fDE3NjQxNTczOTR8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1525382455947-f319bc05fb35?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHw0fHxwYW5kYXxlbnwwfHx8fDE3NjQxNTczOTR8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "koala": [
        "https://images.unsplash.com/photo-1579972383667-4894c883d674?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwxfHxrb2FsYXxlbnwwfHx8fDE3NjQxNTc0MDB8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1579649554660-463ed1d72831?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwzfHxrb2FsYXxlbnwwfHx8fDE3NjQxNTc0MDB8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    
    # INSECTS
    "butterfly": [
        "https://images.unsplash.com/photo-1560263816-d704d83cce0f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwxfHxidXR0ZXJmbHl8ZW58MHx8fHwxNzY0MTU3MzIzfDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1533048324814-79b0a31982f1?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwzfHxidXR0ZXJmbHl8ZW58MHx8fHwxNzY0MTU3MzIzfDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "bee": [
        "https://images.unsplash.com/photo-1568526381923-caf3fd520382?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwxfHxiZWV8ZW58MHx8fHwxNzY0MTU3MzI4fDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1589526261866-ab0d34f8dc19?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwyfHxiZWV8ZW58MHx8fHwxNzY0MTU3MzI4fDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    
    # REPTILES
    "snake": [
        "https://images.unsplash.com/photo-1633081528930-91c8cc07f3d7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzl8MHwxfHNlYXJjaHwxfHxzbmFrZXxlbnwwfHx8fDE3NjQxNTczMzR8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1531386151447-fd76ad50012f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzl8MHwxfHNlYXJjaHw0fHxzbmFrZXxlbnwwfHx8fDE3NjQxNTczMzR8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "lizard": [
        "https://images.unsplash.com/photo-1504450874802-0ba2bcd9b5ae?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwyfHxsaXphcmR8ZW58MHx8fHwxNzY0MTU3MzM5fDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1492963892107-740cd39d9ff3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwzfHxsaXphcmR8ZW58MHx8fHwxNzY0MTU3MzM5fDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "crocodile": [
        "https://images.unsplash.com/photo-1471005197911-88e9d4a7834d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwyfHxjcm9jb2RpbGV8ZW58MHx8fHwxNzY0MTU3Mzg4fDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1611069648374-733e7bb73e5c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwzfHxjcm9jb2RpbGV8ZW58MHx8fHwxNzY0MTU3Mzg4fDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "frog": [
        "https://images.unsplash.com/photo-1496070242169-b672c576566b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxmcm9nfGVufDB8fHx8MTc2NDE1NzM3Mnww&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1559253664-ca249d4608c6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwyfHxmcm9nfGVufDB8fHx8MTc2NDE1NzM3Mnww&ixlib=rb-4.1.0&q=85&w=800"
    ],
    
    # FARM ANIMALS
    "horse": [
        "https://images.unsplash.com/photo-1553284965-83fd3e82fa5a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwxfHxob3JzZXxlbnwwfHx8fDE3NjQxNTczNDR8MA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1593179449458-e0d43d512551?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwyfHxob3JzZXxlbnwwfHx8fDE3NjQxNTczNDR8MA&ixlib=rb-4.1.0&q=85&w=800"
    ],
    "cow": [
        "https://images.unsplash.com/photo-1570042225831-d98fa7577f1e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwxfHxjb3d8ZW58MHx8fHwxNzY0MTU3MzUwfDA&ixlib=rb-4.1.0&q=85&w=800",
        "https://images.unsplash.com/photo-1527153857715-3908f2bae5e8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwyfHxjb3d8ZW58MHx8fHwxNzY0MTU3MzUwfDA&ixlib=rb-4.1.0&q=85&w=800"
    ],
}

def download_image(url, filepath):
    """Download a single image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def main():
    dataset_dir = Path(__file__).parent / "uploads" / "dataset"
    
    total_downloaded = 0
    total_failed = 0
    
    for category, urls in ANIMAL_IMAGES.items():
        category_dir = dataset_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nDownloading {category} images...")
        
        for i, url in enumerate(urls):
            filename = f"{category}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = category_dir / filename
            
            if download_image(url, filepath):
                print(f"  ✓ Downloaded {filename}")
                total_downloaded += 1
            else:
                print(f"  ✗ Failed {filename}")
                total_failed += 1
            
            time.sleep(0.5)  # Be nice to the servers
    
    print(f"\n{'='*50}")
    print(f"Download complete!")
    print(f"Total downloaded: {total_downloaded}")
    print(f"Total failed: {total_failed}")
    print(f"Categories: {len(ANIMAL_IMAGES)}")

if __name__ == "__main__":
    main()
