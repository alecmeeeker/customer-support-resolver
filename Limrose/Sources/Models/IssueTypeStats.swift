import Foundation
import GRDB

struct IssueTypeStats: Codable, FetchableRecord, Identifiable {
    var id: String { issueType ?? "Unknown" }
    var issueType: String?
    var count: Int
    var exampleSummary: String?

    enum CodingKeys: String, CodingKey {
        case issueType = "issue_type"
        case count
        case exampleSummary = "example_summary"
    }
}
