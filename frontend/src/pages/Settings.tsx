import { useEffect, useState } from 'react'
import axios from 'axios'

export function Settings() {
	const jwt = localStorage.getItem('jwt')!
	const [p, setP] = useState<any>(null)
	useEffect(()=>{ axios.get('/api/business/profile', { headers: { Authorization: `Bearer ${jwt}` }}).then(r=> setP(r.data)) }, [])
	async function save() {
		const { data } = await axios.put('/api/business/profile', p, { headers: { Authorization: `Bearer ${jwt}` }})
		setP(data)
	}
	if (!p) return null
	return (
		<div className="bg-white rounded shadow p-4 grid grid-cols-2 gap-3 text-sm">
			<input value={p.name||''} onChange={e=>setP({...p, name: e.target.value})} placeholder="Business name" className="border rounded px-2 py-1" />
			<input value={p.industry||''} onChange={e=>setP({...p, industry: e.target.value})} placeholder="Industry" className="border rounded px-2 py-1" />
			<input type="number" value={p.starting_cash||0} onChange={e=>setP({...p, starting_cash: Number(e.target.value)})} placeholder="Starting cash" className="border rounded px-2 py-1" />
			<input type="number" value={p.monthly_revenue||0} onChange={e=>setP({...p, monthly_revenue: Number(e.target.value)})} placeholder="Monthly revenue" className="border rounded px-2 py-1" />
			<input type="number" value={p.fixed_expenses||0} onChange={e=>setP({...p, fixed_expenses: Number(e.target.value)})} placeholder="Fixed expenses" className="border rounded px-2 py-1" />
			<input type="number" value={p.payment_cycle_days||30} onChange={e=>setP({...p, payment_cycle_days: Number(e.target.value)})} placeholder="Payment cycle days" className="border rounded px-2 py-1" />
			<input type="number" value={p.min_cash_threshold||0} onChange={e=>setP({...p, min_cash_threshold: Number(e.target.value)})} placeholder="Min cash threshold" className="border rounded px-2 py-1" />
			<div className="col-span-2">
				<button onClick={save} className="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
			</div>
		</div>
	)
}