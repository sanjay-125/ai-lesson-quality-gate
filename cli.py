"""CLI Runner for the AI Lesson Quality-Gate System.

Usage:
    python cli.py --topic "Introduction to RAG"
    python cli.py --flaw unexplained_jargon    # Deliberate error injection for demo
"""

import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from src.graph import QualityGateWorkflow

console = Console()


def main():
    parser = argparse.ArgumentParser(description="AI Lesson Quality-Gate Agent")
    parser.add_argument("--topic", type=str, default="Introduction to RAG", help="Topic to teach")
    parser.add_argument(
        "--flaw",
        type=str,
        choices=["none", "unexplained_jargon", "missing_analogy", "poor_chunking"],
        default="none",
        help="Inject deliberate flaw to demonstrate evaluator rejection",
    )
    parser.add_argument("--retries", type=int, default=2, help="Max retries")
    args = parser.parse_args()

    flaw = None if args.flaw == "none" else args.flaw

    console.print(
        Panel.fit(
            f"[bold cyan]AI Lesson Quality-Gate Content System[/bold cyan]\n"
            f"[yellow]Target Audience:[/yellow] Indian Class 12 Graduate (Non-English background, starting AI from zero)\n"
            f"[yellow]Topic:[/yellow] {args.topic}\n"
            f"[yellow]Deliberate Flaw Injection:[/yellow] {flaw or 'None (Standard Generation)'}\n"
            f"[yellow]Approval Bar:[/yellow] Strict 11/11 Rubric Pass",
            border_style="cyan",
        )
    )

    workflow = QualityGateWorkflow(topic=args.topic, max_retries=args.retries)

    for update in workflow.run_step_by_step(deliberate_flaw=flaw):
        step = update["step"]

        if step == "MEMORY_RETRIEVED":
            console.print(f"[bold green]✔[/bold green] {update['message']}")

        elif step == "GENERATED":
            console.print(
                f"\n[bold blue]📝 Iteration {update['iteration']}:[/bold blue] Draft generated ({len(update['markdown'].split())} words)."
            )

        elif step == "EVALUATED":
            eval_out = update["evaluation"]
            score = update["score"]
            passed = update["passed"]

            table = Table(
                title=f"Rubric Evaluation — Iteration {update['iteration']} (Score: {score}/11)",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("ID", width=4, justify="center")
            table.add_column("Rubric Name", width=34)
            table.add_column("Status", width=8, justify="center")
            table.add_column("Evidence / Rationale", width=55)

            for r in eval_out.rubric_results:
                status_str = "[bold green]PASS[/bold green]" if r.score == 1 else "[bold red]FAIL[/bold red]"
                table.add_row(str(r.rubric_id), r.rubric_name, status_str, r.evidence[:85] + ("..." if len(r.evidence) > 85 else ""))

            console.print(table)

            if passed:
                console.print(f"[bold green]🎉 APPROVED & CLEARED FOR SHIPPING! (Score: {score}/11)[/bold green]")
            else:
                console.print(f"[bold red]⛔ REJECTED! (Score: {score}/11 - Approval threshold: 11/11)[/bold red]")
                for issue in eval_out.critical_issues[:3]:
                    console.print(f"  [red]• {issue}[/red]")

        elif step == "REGENERATING":
            console.print(f"\n[bold yellow]🔄 {update['message']}[/bold yellow]")

        elif step == "COMPLETE":
            console.print("\n" + "=" * 70)
            if update["is_approved"]:
                console.print(
                    Panel(
                        f"[bold green]✨ SUCCESS: Final Lesson Approved and Saved to final_output/RAG_Lesson.md![/bold green]\n"
                        f"Rejection audit log saved to [bold]final_output/Rejection_Log.md[/bold]",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        f"[bold red]❌ Loop Terminated: Reached max retries without clearing 11/11.[/bold red]\n"
                        f"Audit log saved to [bold]final_output/Rejection_Log.md[/bold]",
                        border_style="red",
                    )
                )


if __name__ == "__main__":
    main()
