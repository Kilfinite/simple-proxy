import { useEffect } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { Dashboard } from './Dashboard'
import { Auth } from './Auth'
import { Transactions } from './Transactions'
import { Forecast } from './Forecast'
import { Budget } from './Budget'
import { Alerts } from './Alerts'
import { Settings } from './Settings'

export default function App() {
	return (
		<div className="min-h-screen">
			<Nav />
			<div className="max-w-6xl mx-auto p-4">
				<Routes>
					<Route path="/" element={<Dashboard />} />
					<Route path="/auth" element={<Auth />} />
					<Route path="/transactions" element={<Transactions />} />
					<Route path="/forecast" element={<Forecast />} />
					<Route path="/budget" element={<Budget />} />
					<Route path="/alerts" element={<Alerts />} />
					<Route path="/settings" element={<Settings />} />
				</Routes>
			</div>
		</div>
	)
}

function Nav() {
	return (
		<div className="bg-white border-b">
			<div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
				<Link to="/" className="font-semibold text-lg">BizForecast</Link>
				<nav className="flex gap-4 text-sm">
					<Link to="/transactions">Transactions</Link>
					<Link to="/forecast">Forecast</Link>
					<Link to="/budget">Budget</Link>
					<Link to="/alerts">Alerts</Link>
					<Link to="/settings">Settings</Link>
				</nav>
			</div>
		</div>
	)
}