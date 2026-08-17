"""
MISTY Training Knowledge.

Contains the foundational identity and general training data for the
MISTY cognitive system. Identity facts encode who MISTY is: a smart
artificial brain created by Pixline Incorporate (founder Salauddin Mir,
known as Netvai) — India's first smart AI brain without any LLM
dependency. General training facts provide broad baseline knowledge
about the world, India, and the Bengali language so MISTY can converse
meaningfully from the first interaction.

These facts are injected into the knowledge graph and semantic memory
at Brain initialization, and the same facts are flushed to the
persistence database so they survive server restarts.
"""

from dataclasses import dataclass, field
from typing import Dict, List

# ---------------------------------------------------------------------------
# Identity: the core self-knowledge of MISTY
# ---------------------------------------------------------------------------

IDENTITY_CONCEPTS: List[Dict[str, str]] = [
    {"name": "Misty", "type": "AI System"},
    {"name": "Smart Artificial Brain", "type": "Category"},
    {"name": "Pixline Incorporate", "type": "Company"},
    {"name": "Salauddin Mir", "type": "Person"},
    {"name": "Netvai", "type": "Person"},
    {"name": "India", "type": "Country"},
    {"name": "Artificial Intelligence", "type": "Field"},
    {"name": "LLM", "type": "Technology"},
    {"name": "Spiking Neural Network", "type": "Technology"},
    {"name": "Knowledge Graph", "type": "Technology"},
    {"name": "Bengali", "type": "Language"},
    {"name": "Cognitive System", "type": "Category"},
]

IDENTITY_RELATIONS: List[Dict[str, str]] = [
    # self-type
    {"source": "Misty", "target": "Smart Artificial Brain", "type": "is_a"},
    {"source": "Misty", "target": "Cognitive System", "type": "is_a"},
    {"source": "Misty", "target": "Artificial Intelligence", "type": "is_a"},
    # origin and creator
    {"source": "Misty", "target": "Pixline Incorporate", "type": "made_by"},
    {"source": "Misty", "target": "India", "type": "origin"},
    # founder chain
    {"source": "Pixline Incorporate", "target": "Salauddin Mir", "type": "founder"},
    {"source": "Salauddin Mir", "target": "Netvai", "type": "also_known_as"},
    # distinguishing technology facts
    {"source": "Misty", "target": "Spiking Neural Network", "type": "uses"},
    {"source": "Misty", "target": "Knowledge Graph", "type": "uses"},
    {"source": "Misty", "target": "LLM", "type": "without_dependency"},
    # languages
    {"source": "Misty", "target": "Bengali", "type": "speaks"},
    {"source": "Bengali", "target": "Language", "type": "is_a"},
    {"source": "Salauddin Mir", "target": "India", "type": "nationality"},
]

IDENTITY_FACTS: List[Dict[str, str]] = [
    {"subject": "Misty", "predicate": "is_a", "obj": "Smart Artificial Brain"},
    {"subject": "Misty", "predicate": "is_a", "obj": "Cognitive System"},
    {"subject": "Misty", "predicate": "made_by", "obj": "Pixline Incorporate"},
    {"subject": "Misty", "predicate": "creator", "obj": "Salauddin Mir"},
    {"subject": "Misty", "predicate": "origin", "obj": "India"},
    {"subject": "Misty", "predicate": "uses", "obj": "Spiking Neural Network"},
    {"subject": "Misty", "predicate": "uses", "obj": "Knowledge Graph"},
    {"subject": "Misty", "predicate": "without_dependency", "obj": "LLM"},
    {"subject": "Misty", "predicate": "speaks", "obj": "Bengali"},
    {"subject": "Misty", "predicate": "speaks", "obj": "English"},
    {"subject": "Pixline Incorporate", "predicate": "founder", "obj": "Salauddin Mir"},
    {"subject": "Salauddin Mir", "predicate": "also_known_as", "obj": "Netvai"},
    {"subject": "Salauddin Mir", "predicate": "nationality", "obj": "India"},
    {"subject": "Salauddin Mir", "predicate": "role", "obj": "Founder"},
    {"subject": "Misty", "predicate": "tagline", "obj": "India's first smart AI brain without LLM dependency"},
]

# ---------------------------------------------------------------------------
# Bengali Literature: structured, source-backed metadata
# ---------------------------------------------------------------------------

LITERATURE_CONCEPTS: List[Dict[str, str]] = [
    {"name": "Bengali Literature", "type": "Literary Tradition"},
    {"name": "Charyapada", "type": "Ancient Bengali Poetry"},
    {"name": "Vaishnava Padavali", "type": "Medieval Lyric Poetry"},
    {"name": "Mangalkavya", "type": "Medieval Narrative Poetry"},
    {"name": "Bengali Translation Literature", "type": "Literary Movement"},
    {"name": "Bengali Novel", "type": "Literary Genre"},
    {"name": "Bengali Short Story", "type": "Literary Genre"},
    {"name": "Bengali Drama", "type": "Literary Genre"},
    {"name": "Rabindranath Tagore", "type": "Author"},
    {"name": "Bankim Chandra Chattopadhyay", "type": "Author"},
    {"name": "Michael Madhusudan Dutt", "type": "Author"},
    {"name": "Sarat Chandra Chattopadhyay", "type": "Author"},
    {"name": "Kazi Nazrul Islam", "type": "Author"},
    {"name": "Krittibas Ojha", "type": "Author"},
    {"name": "Kashiram Das", "type": "Author"},
    {"name": "Srikrishnakirtan", "type": "Medieval Bengali Text"},
    {"name": "Sri Krishna Vijay", "type": "Medieval Bengali Text"},
    {"name": "Gitanjali", "type": "Poetry Collection"},
    {"name": "Meghnad Badh Kavya", "type": "Epic Poem"},
    {"name": "Anandamath", "type": "Historical Novel"},
    {"name": "Devdas", "type": "Novel"},
    {"name": "Bidrohi", "type": "Poem"},
]

LITERATURE_RELATIONS: List[Dict[str, str]] = [
    {"source": "Bengali Literature", "target": "Charyapada", "type": "includes"},
    {"source": "Bengali Literature", "target": "Vaishnava Padavali", "type": "includes"},
    {"source": "Bengali Literature", "target": "Mangalkavya", "type": "includes"},
    {"source": "Bengali Literature", "target": "Bengali Novel", "type": "includes"},
    {"source": "Bengali Literature", "target": "Bengali Short Story", "type": "includes"},
    {"source": "Bengali Literature", "target": "Bengali Drama", "type": "includes"},
    {"source": "Rabindranath Tagore", "target": "Gitanjali", "type": "wrote"},
    {"source": "Bankim Chandra Chattopadhyay", "target": "Anandamath", "type": "wrote"},
    {"source": "Michael Madhusudan Dutt", "target": "Meghnad Badh Kavya", "type": "wrote"},
    {"source": "Sarat Chandra Chattopadhyay", "target": "Devdas", "type": "wrote"},
    {"source": "Kazi Nazrul Islam", "target": "Bidrohi", "type": "wrote"},
    {"source": "Krittibas Ojha", "target": "Bengali Ramayana", "type": "translated"},
    {"source": "Kashiram Das", "target": "Bengali Mahabharata", "type": "translated"},
]

LITERATURE_FACTS: List[Dict[str, str]] = [
    {"subject": "Bengali Literature", "predicate": "periods", "obj": "ancient, medieval, and modern"},
    {"subject": "Bengali Literature", "predicate": "ancient_period", "obj": "approximately 650-1200"},
    {"subject": "Bengali Literature", "predicate": "medieval_period", "obj": "approximately 1200-1800"},
    {"subject": "Bengali Literature", "predicate": "modern_period", "obj": "from approximately 1800 onward"},
    {
        "subject": "Charyapada",
        "predicate": "description",
        "obj": "earliest extant specimens of ancient Bangla devotional verse",
    },
    {"subject": "Vaishnava Padavali", "predicate": "theme", "obj": "Radha and Krishna devotional lyrics"},
    {
        "subject": "Mangalkavya",
        "predicate": "description",
        "obj": "medieval narrative poems praising deities and depicting social life",
    },
    {
        "subject": "Krittibas Ojha",
        "predicate": "contribution",
        "obj": "early influential Bengali rendering of the Ramayana",
    },
    {
        "subject": "Kashiram Das",
        "predicate": "contribution",
        "obj": "widely influential Bengali rendering of the Mahabharata",
    },
    {
        "subject": "Rabindranath Tagore",
        "predicate": "literary_roles",
        "obj": "poet, novelist, dramatist, short-story writer, and essayist",
    },
    {
        "subject": "Michael Madhusudan Dutt",
        "predicate": "contribution",
        "obj": "pioneered Bengali blank verse and modern epic drama",
    },
    {
        "subject": "Bankim Chandra Chattopadhyay",
        "predicate": "contribution",
        "obj": "major pioneer of the modern Bengali novel",
    },
    {
        "subject": "Sarat Chandra Chattopadhyay",
        "predicate": "contribution",
        "obj": "known for accessible novels and social realism",
    },
    {
        "subject": "Kazi Nazrul Islam",
        "predicate": "contribution",
        "obj": "poet and writer associated with rebellion, equality, and humanism",
    },
    {"subject": "Gitanjali", "predicate": "genre", "obj": "poetry collection by Rabindranath Tagore"},
    {
        "subject": "Meghnad Badh Kavya",
        "predicate": "genre",
        "obj": "modern Bengali epic poem by Michael Madhusudan Dutt",
    },
    {"subject": "Anandamath", "predicate": "genre", "obj": "historical novel by Bankim Chandra Chattopadhyay"},
    {"subject": "Devdas", "predicate": "genre", "obj": "novel by Sarat Chandra Chattopadhyay"},
    {"subject": "Bidrohi", "predicate": "genre", "obj": "revolutionary Bengali poem by Kazi Nazrul Islam"},
    {"subject": "Misty", "predicate": "has_domain", "obj": "structured Bengali Literature metadata and summaries"},
]


# ---------------------------------------------------------------------------
# General training knowledge — baseline world knowledge
# ---------------------------------------------------------------------------

TRAINING_FACTS: List[Dict[str, str]] = [
    # India
    {"subject": "India", "predicate": "is_a", "obj": "Country"},
    {"subject": "India", "predicate": "capital", "obj": "New Delhi"},
    {"subject": "India", "predicate": "continent", "obj": "Asia"},
    # Bengali language
    {"subject": "Bengali", "predicate": "spoken_in", "obj": "India"},
    {"subject": "Bengali", "predicate": "spoken_in", "obj": "Bangladesh"},
    {"subject": "Bengali", "predicate": "region", "obj": "West Bengal"},
    # Technology
    {"subject": "Artificial Intelligence", "predicate": "is_a", "obj": "Field of computer science"},
    {"subject": "Spiking Neural Network", "predicate": "is_a", "obj": "Neural network model"},
    {"subject": "Spiking Neural Network", "predicate": "mimics", "obj": "Biological neurons"},
    {"subject": "Knowledge Graph", "predicate": "is_a", "obj": "Graph of entities and relations"},
    {"subject": "LLM", "predicate": "is_a", "obj": "Large language model"},
    {"subject": "LLM", "predicate": "requires", "obj": "Massive compute"},
    # Science basics
    {"subject": "Sun", "predicate": "is_a", "obj": "Star"},
    {"subject": "Earth", "predicate": "orbits", "obj": "Sun"},
    {"subject": "Water", "predicate": "formula", "obj": "H2O"},
    {"subject": "Human", "predicate": "is_a", "obj": "Species"},
    {"subject": "Human", "predicate": "brain", "obj": "Contains neurons"},
    {"subject": "Neuron", "predicate": "is_a", "obj": "Nerve cell"},
    # Time and self-awareness
    {"subject": "Misty", "predicate": "goal", "obj": "Learn, remember, and reason without LLMs"},
    {"subject": "Misty", "predicate": "lives_on", "obj": "https://misty-brain.onrender.com"},
]


@dataclass
class TrainingPackage:
    """A package of identity and general training data for the brain."""

    concepts: List[Dict[str, str]] = field(default_factory=list)
    relations: List[Dict[str, str]] = field(default_factory=list)
    facts: List[Dict[str, str]] = field(default_factory=list)


def identity_package() -> TrainingPackage:
    """Return MISTY's core self-knowledge package."""
    return TrainingPackage(
        concepts=IDENTITY_CONCEPTS,
        relations=IDENTITY_RELATIONS,
        facts=IDENTITY_FACTS,
    )


def general_training_package() -> TrainingPackage:
    """Return the general baseline training knowledge package."""
    return TrainingPackage(facts=TRAINING_FACTS)


def literature_package() -> TrainingPackage:
    """Return structured Bengali Literature metadata and summaries."""
    return TrainingPackage(
        concepts=LITERATURE_CONCEPTS,
        relations=LITERATURE_RELATIONS,
        facts=LITERATURE_FACTS,
    )


def combined_package() -> TrainingPackage:
    """Return identity, general, mathematics, Physics, and literature data."""
    from brain.math_engine import mathematics_package
    from brain.physics_engine import physics_package

    identity = identity_package()
    general = general_training_package()
    literature = literature_package()
    math_concepts, math_relations, math_facts = mathematics_package()
    physics_concepts, physics_relations, physics_facts = physics_package()
    return TrainingPackage(
        concepts=identity.concepts + literature.concepts + math_concepts + physics_concepts,
        relations=identity.relations + literature.relations + math_relations + physics_relations,
        facts=identity.facts + general.facts + literature.facts + math_facts + physics_facts,
    )
