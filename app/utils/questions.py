import os
import json

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

# Administration self-review questions (example set; adjust as needed)
administration_questions = [
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
  # LEADERSHIP SKILLS
  {"id": 1, "question": "Ability to guide and motivate the crew through example and direction", "type": "scale", "category": "LEADERSHIP SKILLS", "category_description": "Ability to guide and motivate the crew through example and direction"},
  {"id": 2, "question": "Awareness: Is alert to needs / problems of company and its employees", "type": "scale", "category": "LEADERSHIP SKILLS"},
  {"id": 3, "question": "Innovation and Creativity: Generates new ideas and finds novel applications; encourages others to do so", "type": "scale", "category": "LEADERSHIP SKILLS"},
  {"id": 4, "question": "Judgement: Implements sound decisions or timely actions based on available data", "type": "scale", "category": "LEADERSHIP SKILLS"},
  {"id": 5, "question": "Motivation: Stimulates employees to achieve desired results through positive attitude and methods", "type": "scale", "category": "LEADERSHIP SKILLS"},
  {"id": 6, "question": "Team Building: Participates, builds and maintains productive working relationships with superiors, peers and subordinates", "type": "scale", "category": "LEADERSHIP SKILLS"},
  {"id": 7, "question": "Safety Culture: Leads by example to ensure corporate culture reflects the commitment of senior management", "type": "scale", "category": "LEADERSHIP SKILLS"},

  # SUPERVISORY SKILLS
  {"id": 8, "question": "Ability to organize work, assign tasks effectively, monitor progress, and ensure crews meet deadlines and quality standards. As well as their decision-making, problem-solving, and ability to manage different personalities", "type": "scale", "category": "SUPERVISORY SKILLS", "category_description": "Ability to organize work, assign tasks, monitor progress and ensure quality and deadlines"},
  {"id": 9, "question": "Conflict Management: Identifies causes and resolves issues resulting in unproductive organizational and employee disputes", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 10, "question": "Delegation: Capitalizes the full potential of all employees on site", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 11, "question": "Employee Appraisal: Evaluates employee performance fairly and objectively in accordance with company procedure", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 12, "question": "Employee & Pay Equity Support: Knowledge of and adherence to the company’s Payroll policies and procedures", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 13, "question": "Financial Management: Understands budgeting, material, tools, labor and equipment needs", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 14, "question": "Human Resources Planning: Identifies best possible staff for current and future needs", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 15, "question": "Leadership: Inspires productive achievement in subordinates; provides environment for self-motivation; has ability to coach and train others", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 16, "question": "Organization: Arranges and delegates work for effective accomplishment of results", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 17, "question": "Planning: Predetermines results to be achieved and the course of action required to achieve them ahead of time", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 18, "question": "Reviewing: Monitors and modifies work to ensure progress toward desired results", "type": "scale", "category": "SUPERVISORY SKILLS"},
  {"id": 19, "question": "Team Management: Efficiently plans and prioritizes time and resources to improve productivity", "type": "scale", "category": "SUPERVISORY SKILLS"},

  # SAFETY AND ACCOUNTABILITY
  {"id": 20, "question": "Hazard Identification: Leads the hazard identification process for area of responsibility and identifies potential problems before loss occurs", "type": "scale", "category": "SAFETY AND ACCOUNTABILITY", "category_description": "Measures the supervisor’s commitment to maintaining a safe work environment and enforcing safety procedures"},
  {"id": 21, "question": "Inspection: Inspects informally and formally to ensure worker compliance with established rules, policies, procedures and OH&S legislation", "type": "scale", "category": "SAFETY AND ACCOUNTABILITY"},
  {"id": 22, "question": "Incident Investigation: Provides timely reports to senior management of workplace incidents and accidents and encourages worker reporting of non-loss related incidents", "type": "scale", "category": "SAFETY AND ACCOUNTABILITY"},
  {"id": 23, "question": "Reporting: Can complete and submit company safety forms, including daily site safety plans and tool box talks, correctly and on time", "type": "scale", "category": "SAFETY AND ACCOUNTABILITY"},
  {"id": 24, "question": "Assurance: Ensures workers have access to all basic and specialized safety PPE, equipment and tools to do their job safely", "type": "scale", "category": "SAFETY AND ACCOUNTABILITY"},
  {"id": 25, "question": "Safety Communication: Communicates with the MK Safety Team in a respectful and cooperative manner", "type": "scale", "category": "SAFETY AND ACCOUNTABILITY"},

  # COMMUNICATION SKILLS
  {"id": 26, "question": "Team Commitment: Cooperates in working with others to achieve common objectives. Actively contributes to team goals", "type": "scale", "category": "COMMUNICATION SKILLS", "category_description": "Ability to clearly and effectively communicate with crew, peers, and management"},
  {"id": 27, "question": "Communication Channels: Keeps manager and associates aware of important matters in timely fashion, maintains confidentiality", "type": "scale", "category": "COMMUNICATION SKILLS"},
  {"id": 28, "question": "Interdepartmental Coordination: Interacts with other departments to achieve company goals", "type": "scale", "category": "COMMUNICATION SKILLS"},
  {"id": 29, "question": "Interpersonal: Interacts productively with others and is cooperative, maintains enthusiasm and sense of humor", "type": "scale", "category": "COMMUNICATION SKILLS"},
  {"id": 30, "question": "Oral Communications: Verbally expresses clear ideas, facts, problems, and solutions", "type": "scale", "category": "COMMUNICATION SKILLS"},
  {"id": 31, "question": "Written Communication: Can complete and submit company forms in a correct and timely manner", "type": "scale", "category": "COMMUNICATION SKILLS"},

  # GROWTH AND DEVELOPMENT
  {"id": 32, "question": "Shows initiative to learn, improve, and take on new responsibilities", "type": "scale", "category": "GROWTH AND DEVELOPMENT", "category_description": "Supervisor’s willingness and ability to grow, adapt, and improve skills"},
  {"id": 33, "question": "Adaptability to learn new skills and procedures", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 34, "question": "Shown progression in work skills", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 35, "question": "Initiative to complete tasks without being told", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 36, "question": "Capability to work independently", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 37, "question": "Willing to learn new skills and work procedures", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},
  {"id": 38, "question": "Open to feedback from others", "type": "scale", "category": "GROWTH AND DEVELOPMENT"},

  # REFLECTION & PLANNING
  {"id": 39, "question": "List some responsibilities in your job duties", "type": "text", "category": "REFLECTION & PLANNING", "category_description": "We value feedback in this section and appreciate honesty"},
  {"id": 40, "question": "Describe your accomplishments in the last year (what were you most proud of?)", "type": "text", "category": "REFLECTION & PLANNING"},
  {"id": 41, "question": "What could the company do differently to help you better perform your job?", "type": "text", "category": "REFLECTION & PLANNING"},
  {"id": 42, "question": "What are the areas in which you most need to improve?", "type": "text", "category": "REFLECTION & PLANNING"},
  {"id": 43, "question": "What other comments or suggestions should be included in this review?", "type": "text", "category": "REFLECTION & PLANNING"},
  {"id": 44, "question": "List some professional goals you have for the next review period", "type": "text", "category": "REFLECTION & PLANNING"},

   # COMPANY VEHICLE AND MACHINERY
  {"id": 45, "question": "Do you drive a company vehicle?", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "category_description": "Does the employee follow company policy and the BC road laws", "controls_group": "vehicle"},
  {"id": 46, "question": "Avoiding parking tickets onsite", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},
  {"id": 47, "question": "Keeping vehicle clean", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},
  {"id": 48, "question": "Has employee received speeding tickets", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},
  {"id": 49, "question": "Driving with care and avoiding damage to vehicle", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},
  {"id": 50, "question": "Respecting and follow company vehicle policy", "type": "yesno", "category": "COMPANY VEHICLE AND MACHINERY", "depends_on_group": "vehicle", "depends_on_value": "Yes"},

]

_overrides = None

def _load_overrides():
  global _overrides
  if _overrides is not None:
    return _overrides
  path = os.path.join("app", "data", "questions_overrides.json")
  if os.path.exists(path):
    try:
      with open(path, "r", encoding="utf-8") as f:
        _overrides = json.load(f)
    except Exception:
      _overrides = {}
  else:
    _overrides = {}
  return _overrides


def get_questions_for_role(role: str):
  r = (role or "").lower().strip()
  overrides = _load_overrides()
  if r in ("administration", "admin"):
    return overrides.get("administration") or administration_questions
  # Backward-compat: treat legacy 'manager' as 'administration'
  if r == "manager":
    return overrides.get("administration") or administration_questions
  if r == "supervisor":
    return overrides.get("supervisor") or supervisor_questions
  return overrides.get("employee") or employee_questions

# Backward compatibility: keep the original name used elsewhere
questions = employee_questions