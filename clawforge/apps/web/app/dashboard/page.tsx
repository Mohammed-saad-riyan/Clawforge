import { redirect } from 'next/navigation'

// Dashboard is now the main page - redirect to /
export default function DashboardPage() {
  redirect('/')
}
