def generate_mcq_prompt(count,topic,grade,description):
    return f"""Imagine you are a school teacher and Generate {count} 
      multiple choice questions for class {grade} on the topic '{topic}'.
      and consider that {description}.
      Only output a valid JSON array — no explanations, no titles, no introductions.
      Example format (do not include any extra text):
      Format:
      [
        {{
          "question": "What is ...?",
          "options": ["A", "B", "C", "D"],
          "answer": "A"
        }},
        ...
      ]
      """

def generate_descriptive_prompt(count,topic,grade,description):
    return f"""Imagine you are a school teacher and Generate {count} 
      descriptive for class {grade} on the topic '{topic}'.
      and consider that {description}.
      Only output a valid JSON array — no explanations, no titles, no introductions.
      Example format (do not include any extra text):
    Format:
    [
      {{
        "question": "What is ...?",
      }},
      ...
    ]
    """

def generate_math_problem_prompt(count,topic,grade,description):
    return f"""Imagine you are a school teacher and Generate {count} 
      math problems for class {grade} on the topic '{topic}'.
      and consider that {description}.
      Only output a valid JSON array — no explanations, no titles, no introductions.
      Example format (do not include any extra text):
    Format:
    [
      {{
        "question": "What is ...?",
      }},
      ...
    ]
    """

def lesson_plan_prompt(topic, grade):
    return f"""Imagine you are a school teacher and Create a structured lesson plan for topic '{topic}' for class {grade}.
    Include objectives, key points, activities, tools, and latest insights.
      Only output a valid JSON array — no explanations, no titles, no introductions.
      Example format (do not include any extra text):
    Return in JSON:
    {{
      "objectives": [],
      "key_points": [],
      "activities": [],
      "tools": [],
      "recent_updates": []
    }}
    """

def descriptive_answer_evaluation_prompt(question, student_answer):
    return f"""Imagine you are a school teacher and evaluate the following descriptive answer for the given quesion.
  Only output a valid JSON array — no explanations, no titles, no introductions.
  Example format (do not include any extra text):

  Question: {question}
  Student Answer: {student_answer}
  Provide a score out of 10 and explain the reasoning.
  Format:
  {{
    "score": 8,
    "explanation": "The student covered ..."
  }}
  """
