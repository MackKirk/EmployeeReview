employee_questions = [
  # WORK STANDARDS
  {"id": 1,  "question": "Quality of work", "type": "scale", "category": "WORK STANDARDS", "category_description": "How effectivly does this person produce high caliber work compared with the acceptance standards of performance"},
  {"id": 2,  "question": "Completing tasks on time", "type": "scale", "category": "WORK STANDARDS"},
  {"id": 3,  "question": "Technical knowledge of the role", "type": "scale", "category": "WORK STANDARDS"},
  {"id": 4,  "question": "Organization and planning with tools and workspace", "type": "scale", "category": "WORK STANDARDS"},
  {"id": 5,  "question": "Efficient use of time and prioritizing productivity / no slacking", "type": "scale", "category": "WORK STANDARDS"},
  {"id": 6,  "question": "Proactivity and initiative", "type": "scale", "category": "WORK STANDARDS"},

  # BEHAVIOUR AND TEAMWORK
  {"id": 7,  "question": "Communication with the team", "type": "scale", "category": "BEHAVIOUR AND TEAMWORK", "category_description": "How effectivly does the worker control thier emotions and interactions with others"},
  {"id": 8,  "question": "Contribution and teamwork", "type": "scale", "category": "BEHAVIOUR AND TEAMWORK"},
  {"id": 9,  "question": "Respectful interactions with coworkers and others", "type": "scale", "category": "BEHAVIOUR AND TEAMWORK"},
  {"id": 10, "question": "Positive attitude at work", "type": "scale", "category": "BEHAVIOUR AND TEAMWORK"},
  {"id": 11, "question": "Dealing with pressure and unusual problems", "type": "scale", "category": "BEHAVIOUR AND TEAMWORK"},
  {"id": 12, "question": "Adapt to changes in workflow", "type": "scale", "category": "BEHAVIOUR AND TEAMWORK"},

  # GROWTH AND DEVELOPMENT
  {"id": 13, "question": "Adaptability to changes", "type": "scale", "category": "GROWTH AND DEVELOPMENT", "category_description": "Has the employee demonstrated the ability to evolve within the company"},
  {"id": 14, "question": "Shown progression in work skills", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 15, "question": "Initiative to complete task without being told", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 16, "question": "Capability to work independently", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 17, "question": "Willing to learn new skills and work procedures", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 18, "question": "Open to feedback from others", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},

  # SKILLS COMPENTANCY
  {"id": 19, "question": "Problem Solving and Decision making", "type": "scale", "category": "SKILLS COMPENTANCY", "category_description": "Employees level of proficiency in the technical and professional skills required for their role"},
  {"id": 20, "question": "Knowledge of daily work procedures on site", "type": "scale", "category": "SKILLS COMPENTANCY"},
  {"id": 21, "question": "Form Fill Capability on company platforms", "type": "scale", "category": "SKILLS COMPENTANCY"},
  {"id": 22, "question": "Tool Knowledge", "type": "scale", "category": "SKILLS COMPENTANCY"},
  {"id": 23, "question": "Material Knowledge", "type": "scale", "category": "SKILLS COMPENTANCY"},
  {"id": 24, "question": "English Language", "type": "scale", "category": "SKILLS COMPENTANCY"},

  # SAFETY
  {"id": 25, "question": "Arriving onsite prepared and wearing PPE", "type": "scale", "category": "SAFETY", "category_description": "Does employee Follow company and site safety guidelines and procedures"},
  {"id": 26, "question": "Following drug and Alch Policy onsite", "type": "scale", "category": "SAFETY"},
  {"id": 27, "question": "Have you recieved any Safey Discipline / Violation notices", "type": "yesno", "category": "SAFETY"},
  {"id": 28, "question": "Awareness of hazards onsite", "type": "scale", "category": "SAFETY"},
  {"id": 29, "question": "Accountability", "type": "scale", "category": "SAFETY"},
  {"id": 30, "question": "Use of equipment and tools in a safe manner", "type": "scale", "category": "SAFETY"},
  {"id": 31, "question": "Phone use and distraction", "type": "scale", "category": "SAFETY"},

  # RESPONSIBILTY
  {"id": 32, "question": "Use and Care of company tools and equipment", "type": "scale", "category": "RESPONSIBILTY", "category_description": "Does the employee show respect and care for company resources and culture"},
  {"id": 33, "question": "Punctuality", "type": "scale", "category": "RESPONSIBILTY"},
  {"id": 34, "question": "Attendance", "type": "scale", "category": "RESPONSIBILTY"},
  {"id": 35, "question": "Reporting Hours on time / Correctly", "type": "scale", "category": "RESPONSIBILTY"},
  {"id": 36, "question": "Ensuring you arrive onsite prepared with your own PPE", "type": "scale", "category": "RESPONSIBILTY"},
  {"id": 37, "question": "Care for PPE given to you by the company", "type": "scale", "category": "RESPONSIBILTY"},

  # COMPANY VEHICLE AND MACHINERY
  {"id": 38, "question": "Do you drive a company vehicle?", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "category_description": "Does the employee follow company policy and the BC road laws", "controls_group": "vehicle"},
  {"id": 39, "question": "Avoiding parking tickets onsite", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},
  {"id": 40, "question": "Keeping vehicle clean", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},
  {"id": 41, "question": "Has employee received speeding tickets", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},
  {"id": 42, "question": "Driving with care and avoiding damage to vehicle", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},
  {"id": 43, "question": "Respecting and follow company vehicle policy", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},

  # REFLECTION & PLANNING
  {"id": 44, "question": "What do you consider your biggest contribution this cycle?", "type": "text", "category": "REFLECTION & PLANNING", "category_description": "We value feedback in this section and we appricate honesty"},
  {"id": 45, "question": "What challenges did you face and how did you handle them?", "type": "text", "category": "REFLECTION & PLANNING"},
  {"id": 46, "question": "What skills or behaviors would you like to improve?", "type": "text", "category": "REFLECTION & PLANNING"},
  {"id": 47, "question": "What are your professional or personal development goals?", "type": "text", "category": "REFLECTION & PLANNING"},
  {"id": 48, "question": "Do you feel supported by your supervisor and the company? What could be improved?", "type": "text", "category": "REFLECTION & PLANNING"},
  {"id": 49, "question": "Any additional comments or suggestions?", "type": "text", "category": "REFLECTION & PLANNING"}
]

# Manager self-review questions (example set; adjust as needed)
manager_questions = [
  {"id": 101, "question": "Team goal setting and alignment", "type": "scale", "category": "Leadership"},
  {"id": 102, "question": "Coaching and feedback quality", "type": "scale", "category": "Leadership"},
  {"id": 103, "question": "Delegation and empowerment", "type": "scale", "category": "Leadership"},
  {"id": 104, "question": "Cross-team communication", "type": "scale", "category": "Collaboration"},
  {"id": 105, "question": "Project delivery predictability", "type": "scale", "category": "Execution"},
  {"id": 106, "question": "Risk identification and mitigation", "type": "scale", "category": "Execution"},
  {"id": 107, "question": "Hiring and talent development", "type": "scale", "category": "People"},
  {"id": 108, "question": "Performance management", "type": "scale", "category": "People"},
  {"id": 109, "question": "Stakeholder satisfaction", "type": "scale", "category": "Impact"},
  {"id": 110, "question": "Budget awareness and resource use", "type": "scale", "category": "Impact"},
  {"id": 111, "question": "Major impact this cycle", "type": "text", "category": "Reflection & Planning"},
  {"id": 112, "question": "Top 1-2 improvements to focus on", "type": "text", "category": "Reflection & Planning"}
]

# Supervisor self-review questions (example set; adjust as needed)
supervisor_questions = [
  {"id": 201, "question": "Clarity of expectations set for team", "type": "scale", "category": "Team Management"},
  {"id": 202, "question": "Quality of task assignment and follow-up", "type": "scale", "category": "Team Management"},
  {"id": 203, "question": "Safety enforcement and compliance", "type": "scale", "category": "Safety"},
  {"id": 204, "question": "Shift planning and attendance oversight", "type": "scale", "category": "Operations"},
  {"id": 205, "question": "Issue escalation and resolution", "type": "scale", "category": "Operations"},
  {"id": 206, "question": "Communication up and down the chain", "type": "scale", "category": "Communication"},
  {"id": 207, "question": "Training and onboarding support", "type": "scale", "category": "People"},
  {"id": 208, "question": "Top contribution this cycle", "type": "text", "category": "Reflection & Planning"},
  {"id": 209, "question": "Areas to improve next cycle", "type": "text", "category": "Reflection & Planning"}
]

def get_questions_for_role(role: str):
  r = (role or "").lower().strip()
  if r == "manager":
    return manager_questions
  if r == "supervisor":
    return supervisor_questions
  return employee_questions

# Backward compatibility: keep the original name used elsewhere
questions = employee_questions