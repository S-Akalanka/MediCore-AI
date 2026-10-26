from dataclasses import dataclass

from nawaloka.agents.messages import ChartSpec


@dataclass(frozen=True)
class Panel:
    key: str
    title: str
    question: str
    sql: str
    chart: ChartSpec


PANELS = [
    Panel(
        key="revenue_trend",
        title="Revenue Trend",
        question="Monthly invoiced revenue",
        sql="""
            SELECT CAST(DATE_TRUNC('month', invoice_date) AS date) AS month, SUM(net_amount) AS revenue
            FROM billing_invoices
            WHERE invoice_date BETWEEN :start AND :end
            GROUP BY 1 ORDER BY 1
        """,
        chart=ChartSpec("line", "month", "revenue", "Monthly Revenue", "Month", "Revenue"),
    ),
    Panel(
        key="top_diagnoses",
        title="Top Diagnoses",
        question="Most common diagnoses",
        sql="""
            SELECT diagnosis_description AS diagnosis, COUNT(*) AS cases
            FROM diagnoses
            WHERE diagnosis_date BETWEEN :start AND :end
            GROUP BY 1 ORDER BY 2 DESC LIMIT 10
        """,
        chart=ChartSpec("bar", "diagnosis", "cases", "Top 10 Diagnoses", "Diagnosis", "Cases"),
    ),
    Panel(
        key="doctor_load",
        title="Doctor Load",
        question="Doctors with the most appointments",
        sql="""
            SELECT d.first_name || ' ' || d.last_name AS doctor, COUNT(*) AS appointments
            FROM appointments a JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.appointment_date BETWEEN :start AND :end
            GROUP BY d.doctor_id, d.first_name, d.last_name ORDER BY 2 DESC LIMIT 10
        """,
        chart=ChartSpec("bar", "doctor", "appointments", "Busiest Doctors", "Doctor", "Appointments"),
    ),
    Panel(
        key="payment_methods",
        title="Payment Methods",
        question="Total payments by payment method",
        sql="""
            SELECT payment_method, SUM(amount) AS total_paid
            FROM payments
            WHERE payment_date BETWEEN :start AND :end
            GROUP BY 1 ORDER BY 2 DESC
        """,
        chart=ChartSpec("pie", "payment_method", "total_paid", "Payments by Method", "Payment Method", "Total Paid"),
    ),
    Panel(
        key="appointment_outcomes",
        title="Appointment Outcomes",
        question="Appointments by status",
        sql="""
            SELECT status, COUNT(*) AS appointments
            FROM appointments
            WHERE appointment_date BETWEEN :start AND :end
            GROUP BY 1 ORDER BY 2 DESC
        """,
        chart=ChartSpec("pie", "status", "appointments", "Appointment Outcomes", "Status", "Appointments"),
    ),
]
