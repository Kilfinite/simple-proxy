import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

export function Auth() {
	const nav = useNavigate()
	const [email, setEmail] = useState('')
	const [password, setPassword] = useState('')
	const [mode, setMode] = useState<'login'|'signup'>('signup')
	const [error, setError] = useState('')

	async function submit() {
		setError('')
		try {
			const url = mode === 'signup' ? '/api/auth/signup' : '/api/auth/login'
			const { data } = await axios.post(url, { email, password })
			localStorage.setItem('jwt', data.token)
			nav('/')
		} catch (e: any) {
			setError(e?.response?.data?.error || 'Failed')
		}
	}

	return (
		<div className="max-w-md mx-auto bg-white p-6 rounded shadow">
			<h1 className="text-xl font-semibold mb-4">{mode === 'signup' ? 'Sign up' : 'Log in'}</h1>
			<div className="space-y-3">
				<input value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" className="w-full border px-3 py-2 rounded" />
				<input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" className="w-full border px-3 py-2 rounded" />
				{error && <div className="text-red-600 text-sm">{error}</div>}
				<button onClick={submit} className="bg-blue-600 text-white px-4 py-2 rounded w-full">Continue</button>
				<button onClick={()=>setMode(mode==='signup'?'login':'signup')} className="text-sm text-gray-600 w-full">Switch to {mode==='signup'?'Log in':'Sign up'}</button>
			</div>
		</div>
	)
}