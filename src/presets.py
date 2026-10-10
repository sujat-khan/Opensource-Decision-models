"""
Pre-built decision scenarios for quick testing.
"""

PRESETS = {
    "📧 Email Triage": {
        "description": "Route a customer email — detect department, urgency, churn risk, and phishing.",
        "state": {
            "from": "customer@acme.com",
            "subject": "Duplicate billing on March invoice #4411",
            "body": "Hi team, we were billed twice for March. Please refund the duplicate before Friday or we will cancel our plan."
        },
        "questions": {
            "department": {
                "type": "choice",
                "instructions": "Which department should handle this email?",
                "criteria": {
                    "billing": "Invoices, payments, refunds",
                    "technical": "Bugs, outages, integrations",
                    "sales": "Pricing, contracts, demos",
                    "other": "Everything else"
                }
            },
            "urgency": {
                "type": "score",
                "instructions": "How urgent is this request?",
                "criteria": ["Not urgent", "Soon", "Critical deadline or blocking issue"]
            },
            "churn_risk": {
                "type": "noul",
                "instructions": "Does the user threaten to cancel or switch to a competitor?"
            },
            "is_phishing": {
                "type": "noul",
                "instructions": "Is this email a phishing or scam attempt?"
            }
        }
    },

    "🛡️ Content Moderation": {
        "description": "Screen user-generated content for spam, toxicity, and recommended action.",
        "state": "FREE MONEY!!! Click here NOW to claim your $10,000 prize! Limited time only! Visit http://totally-legit-prize.example.com",
        "questions": {
            "spam": {
                "type": "noul",
                "instructions": "Is this content spam?"
            },
            "toxicity": {
                "type": "score",
                "instructions": "How toxic is this content?",
                "criteria": ["Not toxic at all", "Mildly inappropriate", "Moderately toxic", "Severely toxic or hateful"]
            },
            "action": {
                "type": "choice",
                "instructions": "What action should be taken on this content?",
                "criteria": {
                    "approve": "Content is safe to publish",
                    "flag_review": "Content needs human review",
                    "remove": "Content should be removed immediately"
                }
            }
        }
    },

    "🎯 Intent Routing": {
        "description": "Classify a customer message into intent categories and assess sentiment.",
        "state": "I've been trying to integrate your API with my Next.js app but keep getting 401 errors. I followed the docs exactly. This is really frustrating — I'm on a tight deadline.",
        "questions": {
            "intent": {
                "type": "choice",
                "instructions": "What is the primary intent of this message?",
                "criteria": {
                    "technical_support": "Needs help with a technical issue or bug",
                    "billing_inquiry": "Question about pricing, invoices, or payments",
                    "feature_request": "Asking for a new feature or capability",
                    "complaint": "Expressing dissatisfaction or filing a complaint",
                    "general_inquiry": "General question not fitting other categories"
                }
            },
            "sentiment": {
                "type": "score",
                "instructions": "What is the overall sentiment of this message?",
                "criteria": ["Very negative", "Somewhat negative", "Neutral", "Somewhat positive", "Very positive"]
            },
            "needs_escalation": {
                "type": "noul",
                "instructions": "Does this message require escalation to a senior agent or manager?"
            }
        }
    },

    "🔧 Tool-Call Safety": {
        "description": "Judge whether an AI agent's proposed tool call could cause harm.",
        "state": 'send_email(to="all-customers", subject="FINAL NOTICE: account will be suspended today", body="Your account will be terminated unless you verify at http://internal-tool.example")',
        "questions": {
            "could_cause_harm": {
                "type": "noul",
                "instructions": "Could this tool call cause harm to users or the system?"
            },
            "risk_level": {
                "type": "score",
                "instructions": "How risky is this tool call?",
                "criteria": ["No risk — safe to execute", "Low risk — minor concerns", "Medium risk — needs review", "High risk — should be blocked"]
            },
            "recommendation": {
                "type": "choice",
                "instructions": "What should the system do with this tool call?",
                "criteria": {
                    "execute": "Safe to execute as-is",
                    "modify": "Execute with modifications",
                    "review": "Hold for human review before executing",
                    "block": "Block this tool call entirely"
                }
            }
        }
    },

    "🔍 Fact Verification": {
        "description": "Assess whether a claim is supported, refuted, or unverifiable from given evidence.",
        "state": {
            "claim": "The Eiffel Tower was built in 1889 and stands 330 meters tall.",
            "evidence": "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris. It was constructed from 1887 to 1889 as the centerpiece of the 1889 World's Fair. The tower is 330 metres (1,083 ft) tall, about the same height as an 81-storey building."
        },
        "questions": {
            "verdict": {
                "type": "choice",
                "instructions": "Based on the evidence, is the claim supported, refuted, or not enough information?",
                "criteria": {
                    "supported": "The evidence directly supports the claim",
                    "refuted": "The evidence contradicts the claim",
                    "insufficient": "The evidence does not contain enough information to judge"
                }
            },
            "confidence_in_evidence": {
                "type": "score",
                "instructions": "How strong is the evidence for or against the claim?",
                "criteria": ["Very weak evidence", "Moderate evidence", "Strong and direct evidence"]
            }
        }
    },

    "💼 Career & Role Decision": {
        "description": "Evaluate skills, learning speed, and market conditions to pick the best career track and assess 90-day hiring odds.",
        "state": {
            "current_skills": "Python, SQL, basic ML algorithms (scikit-learn, pandas), Git, REST APIs",
            "weekly_study_hours": 20,
            "financial_runway_months": 3,
            "target_timeline_days": 90,
            "background": "Software engineer with 2.5 years experience, transitioning into AI/ML",
            "market_demand": "High demand for AI application engineers (LLMs, RAG, agents) and ML deployment"
        },
        "questions": {
            "recommended_track": {
                "type": "choice",
                "instructions": "Given the candidate's skills, timeline, and current market conditions, which career track maximizes hiring probability within 90 days?",
                "criteria": {
                    "ai_engineer": "Focus on LLM app development, RAG systems, agents, and API integrations",
                    "ml_engineer": "Focus on classical ML pipelines, feature engineering, and model deployment (MLOps)",
                    "senior_data_scientist": "Requires deeper statistics, PhD-level math, or extensive senior domain leadership"
                }
            },
            "hiring_probability": {
                "type": "score",
                "instructions": "How realistic is getting hired in the recommended track within 90 days given the candidate's profile?",
                "criteria": ["Unrealistic (<20%)", "Challenging (20-50%)", "Realistic (50-80%)", "High probability (>80%)"]
            },
            "is_30_day_prep_sufficient": {
                "type": "noul",
                "instructions": "Is 30 days of focused 20h/week preparation sufficient to pass initial technical screenings?"
            }
        }
    },

    "✏️ Custom (Blank)": {
        "description": "Start from scratch — define your own state and questions.",
        "state": "",
        "questions": {}
    }
}

