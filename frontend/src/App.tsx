import { useState, useEffect } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Profile {
  game_mode: 'main' | 'ironman' | 'hcim' | 'gim'
  membership: 'f2p' | 'p2p'
  goals: string[]
  playtime_minutes: number
  skills: Record<string, number>
}

interface AdviceItem {
  title: string
  why_now: string
  steps: string[]
}

interface AdviceResponse {
  items: AdviceItem[]
}

const DEFAULT_SKILLS = ['attack', 'strength', 'defence', 'hitpoints', 'ranged', 'magic', 'prayer']

function App() {
  const [profile, setProfile] = useState<Profile>({
    game_mode: 'main',
    membership: 'f2p',
    goals: [],
    playtime_minutes: 0,
    skills: {}
  })
  const [advice, setAdvice] = useState<AdviceItem[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [customSkill, setCustomSkill] = useState('')

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      const response = await fetch(`${API_URL}/profile`)
      const data = await response.json()
      setProfile(data)
    } catch (error) {
      console.error('Failed to load profile:', error)
    }
  }

  const saveProfile = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`${API_URL}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profile),
      })
      if (response.ok) {
        setMessage('Profile saved successfully!')
      } else {
        setMessage('Failed to save profile')
      }
    } catch (error) {
      setMessage('Error saving profile')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const getAdvice = async () => {
    setLoading(true)
    setAdvice([])
    try {
      const response = await fetch(`${API_URL}/advice`, {
        method: 'POST',
      })
      const data: AdviceResponse = await response.json()
      setAdvice(data.items)
    } catch (error) {
      console.error('Failed to get advice:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateSkill = (skill: string, value: number) => {
    setProfile({
      ...profile,
      skills: {
        ...profile.skills,
        [skill]: Math.max(1, Math.min(99, value))
      }
    })
  }

  const addCustomSkill = () => {
    if (customSkill.trim() && !profile.skills[customSkill.toLowerCase()]) {
      setProfile({
        ...profile,
        skills: {
          ...profile.skills,
          [customSkill.toLowerCase()]: 1
        }
      })
      setCustomSkill('')
    }
  }

  const toggleGoal = (goal: string) => {
    setProfile({
      ...profile,
      goals: profile.goals.includes(goal)
        ? profile.goals.filter(g => g !== goal)
        : [...profile.goals, goal]
    })
  }

  const allSkills = [...DEFAULT_SKILLS, ...Object.keys(profile.skills).filter(s => !DEFAULT_SKILLS.includes(s))]

  return (
    <div className="app">
      <header>
        <h1>RuneScape Lite Advisor</h1>
        <p>Get personalized advice for your RuneScape journey</p>
      </header>

      <div className="container">
        <section className="profile-section">
          <h2>Your Profile</h2>
          
          <div className="form-group">
            <label>Game Mode</label>
            <select
              value={profile.game_mode}
              onChange={(e) => setProfile({ ...profile, game_mode: e.target.value as Profile['game_mode'] })}
            >
              <option value="main">Main</option>
              <option value="ironman">Ironman</option>
              <option value="hcim">Hardcore Ironman</option>
              <option value="gim">Group Ironman</option>
            </select>
          </div>

          <div className="form-group">
            <label>Membership</label>
            <select
              value={profile.membership}
              onChange={(e) => setProfile({ ...profile, membership: e.target.value as Profile['membership'] })}
            >
              <option value="f2p">Free-to-Play</option>
              <option value="p2p">Members</option>
            </select>
          </div>

          <div className="form-group">
            <label>Playtime (minutes)</label>
            <input
              type="number"
              value={profile.playtime_minutes}
              onChange={(e) => setProfile({ ...profile, playtime_minutes: parseInt(e.target.value) || 0 })}
              min="0"
            />
          </div>

          <div className="form-group">
            <label>Goals</label>
            <div className="checkbox-group">
              {['questing', 'combat', 'skilling', 'gp', 'diaries'].map(goal => (
                <label key={goal} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={profile.goals.includes(goal)}
                    onChange={() => toggleGoal(goal)}
                  />
                  {goal.charAt(0).toUpperCase() + goal.slice(1)}
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>Skills</label>
            <div className="skills-grid">
              {allSkills.map(skill => (
                <div key={skill} className="skill-input">
                  <label>{skill.charAt(0).toUpperCase() + skill.slice(1)}</label>
                  <input
                    type="number"
                    value={profile.skills[skill] || 1}
                    onChange={(e) => updateSkill(skill, parseInt(e.target.value) || 1)}
                    min="1"
                    max="99"
                  />
                </div>
              ))}
            </div>
            <div className="add-skill">
              <input
                type="text"
                placeholder="Add custom skill..."
                value={customSkill}
                onChange={(e) => setCustomSkill(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addCustomSkill()}
              />
              <button onClick={addCustomSkill}>Add</button>
            </div>
          </div>

          <div className="button-group">
            <button onClick={saveProfile} disabled={loading}>
              {loading ? 'Saving...' : 'Save Profile'}
            </button>
            <button onClick={getAdvice} disabled={loading}>
              {loading ? 'Loading...' : 'Get Advice'}
            </button>
          </div>

          {message && <div className="message">{message}</div>}
        </section>

        <section className="advice-section">
          <h2>Recommendations</h2>
          {advice.length === 0 ? (
            <p className="placeholder">Click "Get Advice" to see recommendations</p>
          ) : (
            <div className="advice-cards">
              {advice.map((item, index) => (
                <div key={index} className="advice-card">
                  <h3>{item.title}</h3>
                  <p className="why-now"><strong>Why now:</strong> {item.why_now}</p>
                  <div className="steps">
                    <strong>Steps:</strong>
                    <ol>
                      {item.steps.map((step, stepIndex) => (
                        <li key={stepIndex}>{step}</li>
                      ))}
                    </ol>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default App

