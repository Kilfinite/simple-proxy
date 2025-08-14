import { useEffect, useState } from 'react'
import axios from 'axios'
import { Link, useNavigate } from 'react-router-dom'

interface Profile {
	name?: string
	industry?: string
	starting_cash: number
	monthly_revenue: number
	fixed_expenses: number
	payment_cycle_days: number
	min_cash_threshold: number
}

export function Dashboard() {
	const nav = useNavigate()
	const [profile, setProfile] = useState<Profile | null>(null)
	const [loading, setLoading] = useState(true)
	const [error, setError] = useState('')

	useEffect(() => {
		const jwt = localStorage.getItem('jwt')
		if (!jwt) {
			nav('/auth')
			return
		}
		axios.get('/api/business/profile', { headers: { Authorization: `Bearer ${jwt}` }})
			.then(r => setProfile(r.data))
			.catch(() => setError('Auth required'))
			.finally(() => setLoading(false))
	}, [])

	if (loading) return <div>Loading...</div>
	if (error) return <div className="text-red-600">{error}</div>
	if (!profile) return null

	return (
		<div className="space-y-6">
			<StarterWizard profile={profile} onChange={setProfile} />
			<div className="bg-white rounded shadow p-4 flex items-center justify-between">
				<div className="text-sm">
					<div>Current cash: ₹{Math.round(profile.starting_cash).toLocaleString('en-IN')}</div>
					<div>Min threshold: ₹{Math.round(profile.min_cash_threshold).toLocaleString('en-IN')}</div>
				</div>
				<Link to="/forecast" className="bg-blue-600 text-white px-4 py-2 rounded">Generate forecast</Link>
			</div>
		</div>
	)
}

function StarterWizard({ profile, onChange }: { profile: Profile, onChange: (p: Profile)=>void }) {
	const jwt = localStorage.getItem('jwt')!
	const [state, setState] = useState<Profile>(profile)
	const [saving, setSaving] = useState(false)
	const [msg, setMsg] = useState('')

	function set<K extends keyof Profile>(k: K, v: Profile[K]) { setState({ ...state, [k]: v }) }

	async function save() {
		setSaving(true)
		setMsg('')
		try {
			const { data } = await axios.put('/api/business/profile', state, { headers: { Authorization: `Bearer ${jwt}` }})
			onChange(data)
			setMsg('Saved')
		} finally { setSaving(false) }
	}

	return (
		<div className="bg-white rounded shadow p-4">
			<h2 className="font-semibold mb-3">Starter Mode</h2>
			<div className="grid grid-cols-2 gap-3 text-sm">
				<input value={state.name||''} onChange={e=>set('name', e.target.value)} placeholder="Business name" className="border px-3 py-2 rounded" />
				<input value={state.industry||''} onChange={e=>set('industry', e.target.value)} placeholder="Industry" className="border px-3 py-2 rounded" />
				<input type="number" value={state.starting_cash} onChange={e=>set('starting_cash', Number(e.target.value))} placeholder="Starting cash" className="border px-3 py-2 rounded" />
				<input type="number" value={state.monthly_revenue} onChange={e=>set('monthly_revenue', Number(e.target.value))} placeholder="Monthly revenue" className="border px-3 py-2 rounded" />
				<input type="number" value={state.fixed_expenses} onChange={e=>set('fixed_expenses', Number(e.target.value))} placeholder="Fixed expenses" className="border px-3 py-2 rounded" />
				<input type="number" value={state.payment_cycle_days} onChange={e=>set('payment_cycle_days', Number(e.target.value))} placeholder="Payment cycle days" className="border px-3 py-2 rounded" />
				<input type="number" value={state.min_cash_threshold} onChange={e=>set('min_cash_threshold', Number(e.target.value))} placeholder="Min cash threshold" className="border px-3 py-2 rounded" />
			</div>
			<div className="flex items-center gap-3 mt-3">
				<button disabled={saving} onClick={save} className="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
				{msg && <div className="text-green-600 text-sm">{msg}</div>}
			</div>
		</div>
	)
}