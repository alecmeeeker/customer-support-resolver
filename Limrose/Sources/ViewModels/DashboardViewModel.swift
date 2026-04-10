import Foundation
import GRDB

@Observable
final class DashboardViewModel {
    var stats = DashboardStats()
    var categories: [CategoryStats] = []
    var topIssueTypes: [IssueTypeStats] = []
    var recentIssues: [CustomerIssue] = []
    var dailyStats: [DailyStat] = []
    var isLoading = false
    var errorMessage: String?
    var lastRefresh: Date?

    var isEmpty: Bool { stats.totalIssues == 0 }

    private var debounceTask: Task<Void, Never>?

    func refresh() {
        debounceTask?.cancel()
        debounceTask = Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(300))
            guard !Task.isCancelled else { return }
            await performRefresh()
        }
    }

    @MainActor
    private func performRefresh() async {
        guard let dbPool = DatabaseManager.shared.dbPool else {
            errorMessage = "Database not connected"
            return
        }
        isLoading = true
        errorMessage = nil

        do {
            let result = try await dbPool.read { db in
                let s = try DashboardQueries.fetchStats(db: db)
                let c = try DashboardQueries.fetchCategories(db: db)
                let t = try DashboardQueries.fetchTopIssueTypes(db: db)
                let r = try DashboardQueries.fetchRecentIssues(db: db)
                let d = try DashboardQueries.fetchDailyStats(db: db)
                return (s, c, t, r, d)
            }
            stats = result.0
            categories = result.1
            topIssueTypes = result.2
            recentIssues = result.3
            dailyStats = result.4
            lastRefresh = Date()
        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }
}
