import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

interface Point { date: string; opening_balance: number; inflow: number; outflow: number; closing_balance: number }

export function Forecast() {
	const jwt = localStorage.getItem('jwt')!
	const [points, setPoints] = useState<Point[]>([])
	const [metrics, setMetrics] = useState<any>({})
	const [insights, setInsights] = useState<string[]>([])
	const [alerts, setAlerts] = useState<any[]>([])
	const [horizon, setHorizon] = useState(30)
	const [scenario, setScenario] = useState({ sales_pct: 0, receivable_delay_days: 0, expense_shock: 0 })
	const [profile, setProfile] = useState<any>(null)

	useEffect(()=>{ axios.get('/api/business/profile', { headers: { Authorization: `Bearer ${jwt}` }}).then(r=> setProfile(r.data)) }, [])

	async function generate() {
		const { data } = await axios.post('/api/forecast/generate', { horizon_days: horizon, granularity: 'daily', scenario }, { headers: { Authorization: `Bearer ${jwt}` }})
		setPoints(data.points)
		setMetrics(data.metrics)
		setAlerts(data.alerts)
		setInsights(data.insights)
	}

	const minThreshold = profile?.min_cash_threshold ?? 0

	return (
		<div className="space-y-4">
			<MetricsHeader metrics={metrics} />
			<ScenarioPanel state={scenario} setState={setScenario} horizon={horizon} setHorizon={setHorizon} onRun={generate} />
			<div className="bg-white rounded shadow p-4">
				<div className="h-72">
					<ResponsiveContainer>
						<LineChart data={points} margin={{left: 16,right: 16}}>
							<XAxis dataKey="date" hide />
							<YAxis tickFormatter={(v)=>`₹${Math.round(v/1000)}k`} width={60} />
							<Tooltip formatter={(v: any)=>`₹${Number(v).toLocaleString('en-IN')}`} labelFormatter={(l)=>l} />
							<ReferenceLine y={minThreshold} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Min cash', position: 'insideTopRight' }} />
							<Line type="monotone" dataKey="closing_balance" stroke="#2563eb" dot={false} strokeWidth={2} />
						</LineChart>
					</ResponsiveContainer>
				</div>
			</div>
			{insights.length>0 && (
				<div className="bg-white rounded shadow p-4">
					<h3 className="font-semibold mb-2">Insights</h3>
					<ul className="list-disc ml-5 text-sm space-y-1">
						{insights.map((i,idx)=>(<li key={idx}>{i}</li>))}
					</ul>
				</div>
			)}
			{alerts.length>0 && (
				<div className="bg-white rounded shadow p-4">
					<h3 className="font-semibold mb-2">Alerts</h3>
					<ul className="text-sm space-y-1">
						{alerts.map((a,idx)=>(<li key={idx} className={a.severity==='crit'? 'text-red-600': a.severity==='warn'?'text-yellow-600':'text-gray-700'}>{a.message}</li>))}
					</ul>
				</div>
			)}
		</div>
	)
}

function ScenarioPanel({ state, setState, horizon, setHorizon, onRun }: any) {
	return (
		<div className="bg-white rounded shadow p-4">
			<h3 className="font-semibold mb-2">Scenario</h3>
			<div className="grid grid-cols-2 gap-4">
				<div>
					<label className="text-sm">Sales %</label>
					<input type="range" min={-50} max={50} value={state.sales_pct*100} onChange={e=>setState({ ...state, sales_pct: Number(e.target.value)/100 })} className="w-full" />
					<div className="text-xs">{Math.round(state.sales_pct*100)}%</div>
				</div>
				<div>
					<label className="text-sm">Receivable delay (days)</label>
					<input type="range" min={0} max={30} value={state.receivable_delay_days} onChange={e=>setState({ ...state, receivable_delay_days: Number(e.target.value) })} className="w-full" />
					<div className="text-xs">{state.receivable_delay_days} days</div>
				</div>
				<div>
					<label className="text-sm">Expense shock (₹)</label>
					<input type="number" value={state.expense_shock} onChange={e=>setState({ ...state, expense_shock: Number(e.target.value) })} className="border rounded px-2 py-1 w-full" />
				</div>
				<div>
					<label className="text-sm">Horizon</label>
					<select value={horizon} onChange={e=>setHorizon(Number(e.target.value))} className="border rounded px-2 py-1 w-full">
						<option value={30}>30 days</option>
						<option value={60}>60 days</option>
						<option value={90}>90 days</option>
					</select>
				</div>
			</div>
			<div className="mt-3">
				<button onClick={onRun} className="bg-blue-600 text-white px-4 py-2 rounded">Generate forecast</button>
			</div>
		</div>
	)
}

function MetricsHeader({ metrics }: any) {
	if (!metrics) return null
	return (
		<div className="grid grid-cols-2 md:grid-cols-4 gap-3">
			<Card label="Gross Burn (mo)" value={metrics.gross_burn_monthly ? `₹${Math.round(metrics.gross_burn_monthly).toLocaleString('en-IN')}` : '-'} />
			<Card label="Net Burn (mo)" value={metrics.net_burn_monthly ? `₹${Math.round(metrics.net_burn_monthly).toLocaleString('en-IN')}` : '-'} />
			<Card label="Runway (months)" value={metrics.runway_months ?? '-'} />
			<Card label="Runway date" value={metrics.runway_date ?? '-'} />
		</div>
	)
}

function Card({ label, value }: { label: string, value: any }) {
	return (
		<div className="bg-white rounded shadow p-4">
			<div className="text-xs text-gray-500">{label}</div>
			<div className="text-lg font-semibold">{value}</div>
		</div>
	)
}