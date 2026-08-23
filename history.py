#!/usr/bin/env python3
"""
CLI Utility to inspect, search, export, and manage tailoring sessions and career domain knowledge stored in the local SQLite Resume Vault.
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.db import get_db, ResumeDatabase


def format_table_row(id_str: str, date_str: str, title_str: str, tokens_str: str, time_str: str, k_str: str = "No") -> str:
    return f"{id_str:<5} | {date_str:<19} | {title_str:<32} | {k_str:<9} | {tokens_str:<7} | {time_str}"


def cmd_list(args, db: ResumeDatabase):
    """List recent tailoring sessions."""
    sessions = db.list_sessions(limit=args.limit, offset=args.offset)
    print("==================================================================================================")
    print("                                   RESUME VAULT - SESSION HISTORY                                 ")
    print("==================================================================================================")
    if not sessions:
        print("[*] No tailoring sessions found in database.")
        print("    Run `python ai_tailor.py` to start tailoring and recording resumes!")
        print("==================================================================================================")
        return

    print(format_table_row("ID", "Date & Time", "Target Job Title", "Tokens", "Latency", "Knowledge"))
    print("-" * 98)
    for s in sessions:
        created = s["created_at"][:19] if s.get("created_at") else "N/A"
        title = (s.get("target_job_title") or "Unknown")[:32]
        tokens = str(s.get("token_count", 0))
        dur = f"{s.get('execution_time_seconds', 0.0):.1f}s"
        has_k = "Yes" if s.get("has_knowledge") else "No"
        print(format_table_row(str(s["id"]), created, title, tokens, dur, has_k))

    print("==================================================================================================")
    print(f"Showing {len(sessions)} sessions. Use `python history.py show <ID>` for detailed view.")


def cmd_show(args, db: ResumeDatabase):
    """Show comprehensive details for a specific tailoring session."""
    session = db.get_session(args.id)
    if not session:
        print(f"[!] Error: Session #{args.id} was not found in the database.", file=sys.stderr)
        sys.exit(1)

    print("=========================================================================================")
    print(f"                              SESSION DETAILS: #{session['id']}                           ")
    print("=========================================================================================")
    print(f"[*] Session UUID:    {session.get('session_uuid')}")
    print(f"[*] Created At:      {session.get('created_at')}")
    print(f"[*] Target Title:    {session.get('target_job_title')}")
    print(f"[*] Model Used:      {session.get('model')} (effort: {session.get('reasoning_effort')})")
    print(f"[*] Execution Stats: {session.get('token_count')} tokens in {session.get('execution_time_seconds', 0):.1f}s")
    print(f"[*] JD Hash:         {session.get('jd_hash')}")

    k_data = session.get("career_knowledge")
    if k_data and "companies" in k_data:
        comp_names = [c.get("company", "Unknown") for c in k_data.get("companies", [])]
        print(f"[*] Career Knowledge: Active ({len(comp_names)} companies: {', '.join(comp_names)})")
    else:
        print("[*] Career Knowledge: None attached")
    print("-----------------------------------------------------------------------------------------")

    # Show JD
    jd_text = session.get("jd_text", "").strip()
    if args.full_jd or len(jd_text) <= 300:
        print("[*] Target Job Description:")
        print(jd_text)
    else:
        print(f"[*] Target Job Description Excerpt (First 300 chars, use --full-jd to see all {len(jd_text)} chars):")
        print(jd_text[:300] + "...")
    print("-----------------------------------------------------------------------------------------")

    # Show Career Knowledge if requested
    if args.show_knowledge and k_data:
        print("[*] Attached Career Domain Knowledge (Ground Truth):")
        for c in k_data.get("companies", []):
            print(f"    • Company: {c.get('company')} ({c.get('industry', 'N/A')})")
            if c.get("core_operations"):
                print(f"      Operations: {c.get('core_operations')}")
            for r in c.get("roles", []):
                print(f"      - Role: {r.get('role')}")
                rules = r.get("domain_boundary_rules", {})
                if rules.get("what_to_include"):
                    print(f"        Include: {rules.get('what_to_include')}")
                if rules.get("what_never_to_include"):
                    print(f"        NEVER Include: {rules.get('what_never_to_include')}")
        print("-----------------------------------------------------------------------------------------")
    elif k_data and not args.show_knowledge:
        print(f"[*] Career Knowledge: Available. Use `python history.py show {args.id} -k` to inspect domain rules.")
        print("-----------------------------------------------------------------------------------------")

    # Show Reasoning if available
    thinking = session.get("thinking_process")
    if thinking and thinking.strip():
        if args.show_reasoning:
            print("[*] AI Reasoning / Thinking Process:")
            print(thinking.strip())
            print("-----------------------------------------------------------------------------------------")
        else:
            print(f"[*] AI Reasoning: Available ({len(thinking.split())} words). Use `python history.py show {args.id} -r` to view.")
            print("-----------------------------------------------------------------------------------------")

    # Show Tailored Summary & Projects
    tailored = session.get("tailored_data")
    if tailored:
        print(f"[*] Professional Summary:\n{tailored.get('summary', 'N/A')}\n")
        
        skills = tailored.get("technical_skills", [])
        print(f"[*] Technical Skills ({len(skills)} categories):")
        for sk in skills:
            print(f"    • {sk.get('category')}: {sk.get('skills')}")
        
        print(f"\n[*] Technical Projects ({len(tailored.get('key_projects', []))} projects):")
        for proj in tailored.get("key_projects", []):
            print(f"    • {proj.get('title')} [{proj.get('tools')}] ({proj.get('dates')})")
            for b in proj.get("bullets", []):
                print(f"      - {b}")

    print("=========================================================================================")
    print(f"Tip: Run `python history.py export {args.id} -o data/resume_data.json` to restore this resume!")


def cmd_search(args, db: ResumeDatabase):
    """Search sessions matching a keyword."""
    results = db.search_sessions(args.keyword, limit=args.limit)
    print("==================================================================================================")
    print(f"                               SEARCH RESULTS FOR: '{args.keyword}'                              ")
    print("==================================================================================================")
    if not results:
        print(f"[*] No sessions matching '{args.keyword}' were found.")
        print("==================================================================================================")
        return

    print(format_table_row("ID", "Date & Time", "Target Job Title", "Tokens", "Latency", "Knowledge"))
    print("-" * 98)
    for s in results:
        created = s["created_at"][:19] if s.get("created_at") else "N/A"
        title = (s.get("target_job_title") or "Unknown")[:32]
        tokens = str(s.get("token_count", 0))
        dur = f"{s.get('execution_time_seconds', 0.0):.1f}s"
        has_k = "Yes" if s.get("has_knowledge") else "No"
        print(format_table_row(str(s["id"]), created, title, tokens, dur, has_k))

    print("==================================================================================================")
    print(f"Found {len(results)} matching sessions.")


def cmd_export(args, db: ResumeDatabase):
    """Export tailored resume JSON from a specific session."""
    out_path = Path(args.output)
    try:
        saved_file = db.export_session_data(args.id, out_path)
        print(f"[+] Successfully exported Session #{args.id} tailored resume to: {saved_file}")
        print("Next step: Run `python build_resume.py` to compile it to a Word document!")
    except Exception as e:
        print(f"[!] Error exporting session #{args.id}: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_knowledge_list(args, db: ResumeDatabase):
    """List all stored career domain knowledge profiles."""
    profiles = db.list_career_knowledge_profiles()
    print("=========================================================================================")
    print("                        RESUME VAULT - CAREER KNOWLEDGE PROFILES                         ")
    print("=========================================================================================")
    if not profiles:
        print("[*] No career knowledge profiles recorded yet.")
        print("    Run `python research_profile.py` to generate and save career domain knowledge!")
        print("=========================================================================================")
        return

    print(f"{'ID':<4} | {'Profile Name':<28} | {'Candidate':<20} | {'Companies':<10} | {'Created At'}")
    print("-" * 89)
    for p in profiles:
        created = p["created_at"][:19] if p.get("created_at") else "N/A"
        p_name = p.get("profile_name", "Unknown")[:28]
        cand = (p.get("candidate_name") or "Unknown")[:20]
        cnt = str(p.get("companies_count", 0))
        print(f"{p['id']:<4} | {p_name:<28} | {cand:<20} | {cnt:<10} | {created}")
    print("=========================================================================================")


def cmd_knowledge_show(args, db: ResumeDatabase):
    """Show details of a stored career knowledge profile."""
    profile = db.get_career_knowledge(args.target)
    if not profile:
        print(f"[!] Error: Knowledge profile '{args.target}' was not found in the database.", file=sys.stderr)
        sys.exit(1)

    print("=========================================================================================")
    print(f"                       CAREER KNOWLEDGE PROFILE: {profile.get('profile_name')}           ")
    print("=========================================================================================")
    print(f"[*] Profile ID:      {profile.get('id')}")
    print(f"[*] Candidate:       {profile.get('candidate_name')}")
    print(f"[*] Created At:      {profile.get('created_at')}")
    print(f"[*] Static Source:   {profile.get('source_static_path')}")
    print("-----------------------------------------------------------------------------------------")

    k_data = profile.get("knowledge_data", {})
    companies = k_data.get("companies", [])
    print(f"[*] Researched Companies ({len(companies)}):")
    for c in companies:
        print(f"\n[Company]: {c.get('company')} ({c.get('industry', 'N/A')})")
        if c.get("core_operations"):
            print(f"  Operations: {c.get('core_operations')}")
        if c.get("enterprise_tech_environment"):
            print(f"  Tech Env:   {c.get('enterprise_tech_environment')}")
        if c.get("domain_kpis_and_metrics"):
            print(f"  KPIs:       {c.get('domain_kpis_and_metrics')}")
        for r in c.get("roles", []):
            print(f"  - Role: {r.get('role')}")
            if r.get("scope_and_responsibilities"):
                print(f"    Scope:   {r.get('scope_and_responsibilities')}")
            if r.get("transferable_technical_skills"):
                print(f"    Skills:  {', '.join(r.get('transferable_technical_skills', []))}")
            rules = r.get("domain_boundary_rules", {})
            if rules.get("what_to_include"):
                print(f"    Include: {rules.get('what_to_include')}")
            if rules.get("what_never_to_include"):
                print(f"    NEVER:   {rules.get('what_never_to_include')}")
    print("=========================================================================================")


def cmd_knowledge_export(args, db: ResumeDatabase):
    """Export a career knowledge profile to a JSON file."""
    out_path = Path(args.output)
    try:
        saved_file = db.export_knowledge_data(args.target, out_path)
        print(f"[+] Successfully exported knowledge profile '{args.target}' to: {saved_file}")
    except Exception as e:
        print(f"[!] Error exporting knowledge profile '{args.target}': {e}", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args, db: ResumeDatabase):
    """Delete a session from database."""
    if not args.yes:
        confirm = input(f"Are you sure you want to permanently delete Session #{args.id}? [y/N]: ")
        if confirm.lower() not in ("y", "yes"):
            print("[*] Deletion cancelled.")
            return

    if db.delete_session(args.id):
        print(f"[+] Session #{args.id} was successfully deleted.")
    else:
        print(f"[!] Error: Session #{args.id} not found or could not be deleted.", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args, db: ResumeDatabase):
    """Show usage and database statistics."""
    stats = db.get_stats()
    print("=========================================================================================")
    print("                               RESUME VAULT - STATISTICS                                 ")
    print("=========================================================================================")
    print(f"[*] Total Tailoring Sessions:    {stats['total_sessions']}")
    print(f"[*] Career Knowledge Profiles:   {stats['total_knowledge_profiles']}")
    print(f"[*] Total Tokens Generated:      {stats['total_tokens']:,}")
    print(f"[*] Avg Execution Time:          {stats['avg_execution_time']}s")
    print("-----------------------------------------------------------------------------------------")
    print("[*] Top Target Job Titles Tailored:")
    if not stats["top_job_titles"]:
        print("    (No records yet)")
    else:
        for item in stats["top_job_titles"]:
            print(f"    • {item['title']}: {item['count']} times")
    print("=========================================================================================")


def main():
    parser = argparse.ArgumentParser(
        description="Local Resume Vault CLI to view, search, and restore past tailoring queries, resumes, and career knowledge."
    )
    parser.add_argument(
        "--db",
        type=str,
        default="data/resume_vault.db",
        help="Path to SQLite database file (default: data/resume_vault.db)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # list command
    list_parser = subparsers.add_parser("list", help="List recent tailoring sessions")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum records to return (default: 20)")
    list_parser.add_argument("--offset", type=int, default=0, help="Offset for pagination (default: 0)")

    # show command
    show_parser = subparsers.add_parser("show", help="Show full details of a tailoring session")
    show_parser.add_argument("id", type=int, help="Session ID to inspect")
    show_parser.add_argument("--full-jd", "-j", action="store_true", help="Display complete Job Description text")
    show_parser.add_argument("--show-reasoning", "-r", action="store_true", help="Display full model reasoning trace")
    show_parser.add_argument("--show-knowledge", "-k", action="store_true", help="Display full career domain knowledge used")

    # search command
    search_parser = subparsers.add_parser("search", help="Search sessions across JDs, titles, and resume content")
    search_parser.add_argument("keyword", type=str, help="Search keyword or term")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # export command
    export_parser = subparsers.add_parser("export", help="Export session resume data to a JSON file")
    export_parser.add_argument("id", type=int, help="Session ID to export")
    export_parser.add_argument("-o", "--output", type=str, default="data/resume_data.json", help="Output file path (default: data/resume_data.json)")

    # knowledge subcommands
    k_list_parser = subparsers.add_parser("knowledge", help="List all stored career domain knowledge profiles")
    
    k_show_parser = subparsers.add_parser("knowledge-show", help="Show details of a career knowledge profile")
    k_show_parser.add_argument("target", type=str, help="Knowledge profile name (e.g. career_knowledge) or ID")

    k_exp_parser = subparsers.add_parser("knowledge-export", help="Export career knowledge to a JSON file")
    k_exp_parser.add_argument("target", type=str, help="Knowledge profile name or ID")
    k_exp_parser.add_argument("-o", "--output", type=str, default="data/career_knowledge.json", help="Output path (default: data/career_knowledge.json)")

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a tailoring session")
    delete_parser.add_argument("id", type=int, help="Session ID to delete")
    delete_parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    # stats command
    subparsers.add_parser("stats", help="Show usage metrics and database statistics")

    args = parser.parse_args()

    db = ResumeDatabase(db_path=args.db)

    if args.command == "list" or args.command is None:
        if not hasattr(args, "limit"):
            args.limit = 20
        if not hasattr(args, "offset"):
            args.offset = 0
        cmd_list(args, db)
    elif args.command == "show":
        cmd_show(args, db)
    elif args.command == "search":
        cmd_search(args, db)
    elif args.command == "export":
        cmd_export(args, db)
    elif args.command == "knowledge":
        cmd_knowledge_list(args, db)
    elif args.command == "knowledge-show":
        cmd_knowledge_show(args, db)
    elif args.command == "knowledge-export":
        cmd_knowledge_export(args, db)
    elif args.command == "delete":
        cmd_delete(args, db)
    elif args.command == "stats":
        cmd_stats(args, db)


if __name__ == "__main__":
    main()
