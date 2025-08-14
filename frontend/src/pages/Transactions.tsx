import { useEffect, useState } from 'react'
import axios from 'axios'

interface Txn {
	id?: number
	date: string
	description?: string
	amount: number
	type: 'income'|'expense'
	category?: string
	source?: string
}

export function Transactions() {
	const jwt = localStorage.getItem('jwt')!
	const [rows, setRows] = useState<Txn[]>([])
	const [loading, setLoading] = useState(true)
	const [file, setFile] = useState<File|null>(null)

	async function load() {
		setLoading(true)
		const { data } = await axios.get('/api/transactions', { headers: { Authorization: `Bearer ${jwt}` }})
		setRows(data)
		setLoading(false)
	}

	useEffect(() => { load() }, [])

	async function addEmpty() {
		const payload: Txn = { date: new Date().toISOString().slice(0,10), amount: 0, type: 'expense', description: '', category: 'Misc' }
		const { data } = await axios.post('/api/transactions', payload, { headers: { Authorization: `Bearer ${jwt}` }})
		setRows([data, ...rows])
	}

	async function save(t: Txn) {
		const { data } = await axios.put(`/api/transactions/${t.id}`, t, { headers: { Authorization: `Bearer ${jwt}` }})
		setRows(rows.map(r => r.id===t.id? data : r))
	}

	async function remove(id: number) {
		await axios.delete(`/api/transactions/${id}`, { headers: { Authorization: `Bearer ${jwt}` }})
		setRows(rows.filter(r => r.id!==id))
	}

	async function importCsv() {
		if (!file) return
		const form = new FormData()
		form.append('file', file)
		await axios.post('/api/transactions/import', form, { headers: { Authorization: `Bearer ${jwt}` }})
		setFile(null)
		await load()
	}

	if (loading) return <div>Loading...</div>

	return (
		<div className="space-y-4">
			<div className="flex items-center gap-3">
				<button onClick={addEmpty} className="bg-blue-600 text-white px-3 py-2 rounded">Add</button>
				<input type="file" accept=".csv,.xlsx" onChange={e=>setFile(e.target.files?.[0]||null)} />
				<button onClick={importCsv} className="bg-gray-800 text-white px-3 py-2 rounded">Import</button>
			</div>
			<table className="w-full text-sm bg-white rounded shadow">
				<thead>
					<tr className="text-left">
						<th className="p-2">Date</th>
						<th className="p-2">Desc</th>
						<th className="p-2">Type</th>
						<th className="p-2">Amount</th>
						<th className="p-2">Category</th>
						<th className="p-2"></th>
					</tr>
				</thead>
				<tbody>
					{rows.map(r => <Row key={r.id} row={r} onSave={save} onDelete={()=>remove(r.id!)} />)}
				</tbody>
			</table>
		</div>
	)
}

function Row({ row, onSave, onDelete }: { row: Txn, onSave: (t: Txn)=>void, onDelete: ()=>void }) {
	const [state, setState] = useState<Txn>(row)
	return (
		<tr>
			<td className="p-2"><input type="date" value={state.date} onChange={e=>setState({ ...state, date: e.target.value })} className="border rounded px-2 py-1" /></td>
			<td className="p-2"><input value={state.description||''} onChange={e=>setState({ ...state, description: e.target.value })} className="border rounded px-2 py-1" /></td>
			<td className="p-2">
				<select value={state.type} onChange={e=>setState({ ...state, type: e.target.value as any })} className="border rounded px-2 py-1">
					<option value="income">income</option>
					<option value="expense">expense</option>
				</select>
			</td>
			<td className="p-2"><input type="number" value={state.amount} onChange={e=>setState({ ...state, amount: Number(e.target.value) })} className="border rounded px-2 py-1 w-32" /></td>
			<td className="p-2"><input value={state.category||''} onChange={e=>setState({ ...state, category: e.target.value })} className="border rounded px-2 py-1" /></td>
			<td className="p-2 text-right">
				<button onClick={()=>onSave(state)} className="text-blue-600 mr-2">Save</button>
				<button onClick={onDelete} className="text-red-600">Delete</button>
			</td>
		</tr>
	)
}