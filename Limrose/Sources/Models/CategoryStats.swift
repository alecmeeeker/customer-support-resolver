import Foundation
import GRDB

struct CategoryStats: Codable, FetchableRecord, Identifiable {
    var id: String { issueCategory ?? "Unknown" }
    var issueCategory: String?
    var count: Int
    var resolvedCount: Int
    var resolutionRate: Double

    enum CodingKeys: String, CodingKey {
        case issueCategory = "issue_category"
        case count
        case resolvedCount = "resolved_count"
        case resolutionRate = "resolution_rate"
    }
}
