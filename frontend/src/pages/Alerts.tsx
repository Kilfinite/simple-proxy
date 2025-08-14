import { useEffect, useState } from 'react'
import axios from 'axios'

export function Alerts() {
	const jwt = localStorage.getItem('jwt')!
	const [rows, setRows] = useState<any[]>([])

	async function load() {
		const { data } = await axios.get('/api/alerts', { headers: { Authorization: `Bearer ${jwt}` }})
		setRows(data)
	}
	async function refresh() {
		await axios.post('/api/alerts/check-latest', {}, { headers: { Authorization: `Bearer ${jwt}` }})
		await load()
	}
	useEffect(()=>{ load() }, [])

	return (
		<div className="space-y-4">
			<div>
				<button onClick={refresh} className="bg-blue-600 text-white px-4 py-2 rounded">Re-evaluate latest</button>
			</div>
			<div className="bg-white rounded shadow">
				<table className="w-full text-sm">
					<thead>
						<tr className="text-left">
							<th className="p-2">Date</th>
							<th className="p-2">Type</th>
							<th className="p-2">Message</th>
							<th className="p-2">Severity</th>
						</tr>
					</thead>
					<tbody>
						{rows.map((r,i)=> (
							<tr key={i} className="border-t">
								<td className="p-2">{r.trigger_date || r.created_at?.slice(0,10)}</td>
								<td className="p-2">{r.type}</td>
								<td className="p-2">{r.message}</td>
								<td className="p-2">
									<span className={r.severity==='crit'?'text-red-600': r.severity==='warn'?'text-yellow-600':'text-gray-700'}>{r.severity}</span>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	)
}