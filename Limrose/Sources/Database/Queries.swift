import Foundation
import GRDB

enum DashboardQueries {

    /// Overall statistics: total issues, resolved, resolution rate, documented fixes
    /// Ported from customer_issue_dashboard.py lines 239-245
    static func fetchStats(db: Database) throws -> DashboardStats {
        guard let row = try Row.fetchOne(db, sql: """
            SELECT
                COUNT(*) as total_issues,
                COALESCE(SUM(CASE WHEN has_resolution THEN 1 ELSE 0 END), 0) as resolved_issues,
                COUNT(DISTINCT CASE WHEN fix_instructions IS NOT NULL THEN id END) as unique_fixes
            FROM customer_issues_v2
        """) else {
            return DashboardStats()
        }
        let total: Int = row["total_issues"]
        let resolved: Int = row["resolved_issues"]
        let fixes: Int = row["unique_fixes"]
        let rate = total > 0 ? (Double(resolved) / Double(total)) * 100.0 : 0.0
        return DashboardStats(
            totalIssues: total,
            resolvedIssues: resolved,
            resolutionRate: rate,
            documentedFixes: fixes
        )
    }

    /// Category breakdown with resolution rates
    /// Ported from customer_issue_dashboard.py lines 254-262
    static func fetchCategories(db: Database) throws -> [CategoryStats] {
        try CategoryStats.fetchAll(db, sql: """
            SELECT
                issue_category,
                COUNT(*) as count,
                SUM(CASE WHEN has_resolution THEN 1 ELSE 0 END) as resolved_count,
                ROUND(100.0 * SUM(CASE WHEN has_resolution THEN 1 ELSE 0 END) / COUNT(*), 1) as resolution_rate
            FROM customer_issues_v2
            GROUP BY issue_category
            ORDER BY count DESC
        """)
    }

    /// Top issue types by frequency
    /// Ported from customer_issue_dashboard.py lines 267-275
    static func fetchTopIssueTypes(db: Database) throws -> [IssueTypeStats] {
        try IssueTypeStats.fetchAll(db, sql: """
            SELECT
                issue_type,
                COUNT(*) as count,
                MAX(issue_summary) as example_summary
            FROM customer_issues_v2
            GROUP BY issue_type
            ORDER BY count DESC
            LIMIT 10
        """)
    }

    /// Most recent 20 issues
    /// Ported from customer_issue_dashboard.py lines 280-290
    static func fetchRecentIssues(db: Database) throws -> [CustomerIssue] {
        try CustomerIssue.fetchAll(db, sql: """
            SELECT
                id, email_id, thread_id, issue_type, issue_category,
                issue_summary, has_resolution, resolution_summary,
                fix_instructions, similarity_score, based_on_issues,
                confidence_level, created_at, updated_at
            FROM customer_issues_v2
            ORDER BY created_at DESC
            LIMIT 20
        """)
    }

    /// Daily issue counts for the last 30 days
    /// Ported from customer_issue_dashboard.py lines 318-326
    static func fetchDailyStats(db: Database) throws -> [DailyStat] {
        try DailyStat.fetchAll(db, sql: """
            SELECT
                date(created_at) as date,
                COUNT(*) as issues,
                COALESCE(SUM(CASE WHEN has_resolution THEN 1 ELSE 0 END), 0) as resolved
            FROM customer_issues_v2
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY date(created_at)
            ORDER BY date
        """)
    }
}

struct DailyStat: Codable, FetchableRecord {
    var date: String?
    var issues: Int
    var resolved: Int
}
