# TwelveLabs Behavioral Detection - Executive Summary

## 🎯 Core Purpose
Detect and analyze candidate behaviors during recorded technical interviews to ensure interview integrity and identify potential cheating or suspicious activities.

---

## 📊 Key Behavioral Metrics We Detect

### 1. **Eye Contact & Focus Patterns** 👁️
**What we measure:**
- **Looking away frequency**: How often candidate looks away from screen
- **Eye movement patterns**: Rapid eye movements suggesting reading from external sources
- **Focus consistency**: Maintaining attention on the coding task

**Why it matters:**
- Indicates if candidate is reading from hidden notes or getting help
- Shows engagement level with the problem
- Reveals potential use of secondary devices

**Detection queries:**
- "person looking away from camera or screen"
- "eyes moving side to side rapidly"
- "person looking down frequently"

---

### 2. **Environmental Integrity** 🏠
**What we measure:**
- **Background consistency**: Changes in environment during interview
- **Multiple people detection**: Other individuals appearing in frame
- **Lighting changes**: Sudden illumination changes suggesting screen switching

**Why it matters:**
- Ensures candidate is alone during assessment
- Detects potential coaching from off-camera
- Identifies environment manipulation

**Detection queries:**
- "multiple people visible in video"
- "background environment changing"
- "person entering or leaving frame"

---

### 3. **Audio Behavioral Patterns** 🎤
**What we measure:**
- **Voice consistency**: Single vs. multiple voices
- **Whispering detection**: Quiet communication with others
- **Background voices**: Other people talking in environment
- **Typing sounds**: Keyboard usage while not coding

**Why it matters:**
- Reveals communication with others during test
- Indicates potential real-time assistance
- Shows use of external resources

**Detection queries:**
- "multiple different voices speaking"
- "whispering or very quiet speaking"
- "keyboard typing sounds during explanation"
- "other people talking in background"

---

### 4. **Device & Resource Usage** 📱
**What we measure:**
- **Phone usage**: Handling mobile devices during interview
- **Secondary screen detection**: Looking at off-camera monitors
- **Reading behaviors**: Eye patterns suggesting reading from papers/devices
- **Tab switching patterns**: Browser focus loss events

**Why it matters:**
- Primary indicator of using external help
- Shows reliance on unauthorized resources
- Indicates potential answer lookup

**Detection queries:**
- "person using phone or mobile device"
- "person reading from paper or another screen"
- "external monitors or screens visible"

---

### 5. **Body Language & Stress Indicators** 🚨
**What we measure:**
- **Excessive movement**: Fidgeting, nervous behaviors
- **Camera manipulation**: Covering or adjusting camera
- **Sudden posture changes**: Leaning away from camera
- **Hand gestures**: Signaling to someone off-camera

**Why it matters:**
- Indicates discomfort with proctoring
- Suggests attempts to hide activities
- Reveals stress from potential cheating

**Detection queries:**
- "excessive movement or fidgeting"
- "camera being covered or obscured"
- "person making hand gestures to someone off-screen"

---

## 📈 Integrity Scoring System

### Overall Integrity Score (0-1 scale)
Calculated from four core metrics:

1. **Eye Contact Consistency (25%)**
   - 1.0 = Maintains focus throughout
   - 0.0 = Frequently looking away

2. **Environment Stability (25%)**
   - 1.0 = No environmental changes
   - 0.0 = Multiple disruptions

3. **Audio Consistency (25%)**
   - 1.0 = Single clear voice
   - 0.0 = Multiple voices/whispers

4. **Focus Score (25%)**
   - 1.0 = Fully engaged with task
   - 0.0 = Distracted/using other devices

### Flagging Thresholds
- **🟢 Clean (0.85-1.0)**: No concerns, normal behavior
- **🟡 Review Suggested (0.7-0.85)**: Minor anomalies detected
- **🔴 Flagged (< 0.7)**: Requires manual review

---

## 🎬 Behavioral Timeline Output

For each detected behavior, we provide:

```json
{
  "timestamp": "03:45-03:52",
  "behavior": "looking_away",
  "confidence": 0.87,
  "severity": "high",
  "description": "Candidate looking away from screen for extended period",
  "action": "Flag for review"
}
```

---

## 🔍 What Makes a Session Suspicious?

### High Priority Flags (Automatic Review)
- Multiple people detected in frame
- Phone usage during coding
- Multiple voices in audio
- Camera obstruction/manipulation

### Medium Priority Flags (Threshold-based)
- Frequent looking away (>5 times)
- Reading from external sources
- Environment changes
- Whispering detected

### Low Priority Flags (Noted but not critical)
- Excessive fidgeting
- Background noise
- Minor lighting changes
- Brief focus loss

---

## 📋 Candidate Profile Integration

### Proctoring Metrics Added to Profile:
```javascript
{
  "proctoring_metrics": {
    "overall_integrity_score": 0.92,  // Average across all sessions
    "behavioral_consistency": {
      "maintains_eye_contact": true,
      "stable_environment": true,
      "no_external_help": true
    },
    "session_history": [
      {
        "date": "2024-01-15",
        "integrity_score": 0.95,
        "flags": []
      },
      {
        "date": "2024-01-20",
        "integrity_score": 0.89,
        "flags": ["brief_phone_check"]
      }
    ],
    "review_status": "verified_clean"
  }
}
```

---

## 🎯 Detection Examples

### Clean Interview Behavior
- Maintains eye contact with screen
- Thinks out loud while coding
- Natural pauses for thinking
- Consistent environment
- Single voice throughout

### Suspicious Interview Behavior
- Frequently looks to the side (reading notes?)
- Long pauses with typing sounds (messaging someone?)
- Whispers or mutes during problem-solving
- Phone appears in frame
- Multiple voices heard

---

## 🚀 Key Benefits

1. **Automated Screening**: 90% of clean interviews need no manual review
2. **Evidence-Based**: Every flag has video timestamp proof
3. **Fair Assessment**: Consistent criteria applied to all candidates
4. **Time Efficient**: 2-minute analysis per hour of video
5. **Transparent**: Candidates can see what behaviors are monitored

---

## ⚖️ Ethical Considerations

### We DO Monitor:
- Behavioral patterns indicating potential cheating
- Environmental consistency
- Focus and engagement levels
- Audio patterns for multiple participants

### We DON'T Monitor:
- Personal appearance or demographics
- Room details unrelated to integrity
- Natural behaviors (stretching, drinking water)
- Technical struggles or errors

---

## 📊 Success Metrics

- **Detection Accuracy**: >85% true positive rate for cheating behaviors
- **False Positive Rate**: <10% clean sessions flagged
- **Processing Speed**: <2 minutes per video hour
- **Review Efficiency**: 70% reduction in manual review time
- **Candidate Satisfaction**: <5% dispute rate on flags

---

## 🔄 Continuous Improvement

The system learns and improves through:
1. Manual review feedback on flagged sessions
2. Adjustment of confidence thresholds
3. Addition of new behavioral patterns
4. Regular bias testing and calibration