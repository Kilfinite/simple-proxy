import { useEffect, useState } from 'react'
import axios from 'axios'

interface Item { id?: number; name: string; amount: number; cadence: 'monthly'|'weekly'|'daily'; type: 'fixed'|'variable' }

export function Budget() {
	const jwt = localStorage.getItem('jwt')!
	const [items, setItems] = useState<Item[]>([])
	const [newItem, setNewItem] = useState<Item>({ name: '', amount: 0, cadence: 'monthly', type: 'fixed' })

	async function load() {
		const { data } = await axios.get('/api/budget/items', { headers: { Authorization: `Bearer ${jwt}` }})
		setItems(data)
	}
	useEffect(()=>{ load() }, [])

	async function add() {
		const { data } = await axios.post('/api/budget/items', newItem, { headers: { Authorization: `Bearer ${jwt}` }})
		setItems([data, ...items])
		setNewItem({ name: '', amount: 0, cadence: 'monthly', type: 'fixed' })
	}
	async function save(item: Item) {
		const { data } = await axios.put(`/api/budget/items/${item.id}`, item, { headers: { Authorization: `Bearer ${jwt}` }})
		setItems(items.map(i=>i.id===item.id? data : i))
	}
	async function remove(id: number) {
		await axios.delete(`/api/budget/items/${id}`, { headers: { Authorization: `Bearer ${jwt}` }})
		setItems(items.filter(i=>i.id!==id))
	}

	return (
		<div className="space-y-4">
			<div className="bg-white rounded shadow p-4 grid grid-cols-4 gap-3 text-sm">
				<input value={newItem.name} onChange={e=>setNewItem({ ...newItem, name: e.target.value })} placeholder="Name" className="border rounded px-2 py-1" />
				<input type="number" value={newItem.amount} onChange={e=>setNewItem({ ...newItem, amount: Number(e.target.value) })} placeholder="Amount" className="border rounded px-2 py-1" />
				<select value={newItem.cadence} onChange={e=>setNewItem({ ...newItem, cadence: e.target.value as any })} className="border rounded px-2 py-1">
					<option value="monthly">monthly</option>
					<option value="weekly">weekly</option>
					<option value="daily">daily</option>
				</select>
				<select value={newItem.type} onChange={e=>setNewItem({ ...newItem, type: e.target.value as any })} className="border rounded px-2 py-1">
					<option value="fixed">fixed</option>
					<option value="variable">variable</option>
				</select>
				<div className="col-span-4">
					<button onClick={add} className="bg-blue-600 text-white px-4 py-2 rounded">Add</button>
				</div>
			</div>
			<table className="w-full text-sm bg-white rounded shadow">
				<thead>
					<tr className="text-left">
						<th className="p-2">Name</th>
						<th className="p-2">Amount</th>
						<th className="p-2">Cadence</th>
						<th className="p-2">Type</th>
						<th className="p-2"></th>
					</tr>
				</thead>
				<tbody>
					{items.map(i=> <Row key={i.id} item={i} onSave={save} onDelete={()=>remove(i.id!)} />)}
				</tbody>
			</table>
		</div>
	)
}

function Row({ item, onSave, onDelete }: { item: Item, onSave: (i: Item)=>void, onDelete: ()=>void }) {
	const [state, setState] = useState<Item>(item)
	return (
		<tr>
			<td className="p-2"><input value={state.name} onChange={e=>setState({ ...state, name: e.target.value })} className="border rounded px-2 py-1" /></td>
			<td className="p-2"><input type="number" value={state.amount} onChange={e=>setState({ ...state, amount: Number(e.target.value) })} className="border rounded px-2 py-1 w-32" /></td>
			<td className="p-2">
				<select value={state.cadence} onChange={e=>setState({ ...state, cadence: e.target.value as any })} className="border rounded px-2 py-1">
					<option value="monthly">monthly</option>
					<option value="weekly">weekly</option>
					<option value="daily">daily</option>
				</select>
			</td>
			<td className="p-2">
				<select value={state.type} onChange={e=>setState({ ...state, type: e.target.value as any })} className="border rounded px-2 py-1">
					<option value="fixed">fixed</option>
					<option value="variable">variable</option>
				</select>
			</td>
			<td className="p-2 text-right">
				<button onClick={()=>onSave(state)} className="text-blue-600 mr-2">Save</button>
				<button onClick={onDelete} className="text-red-600">Delete</button>
			</td>
		</tr>
	)
}