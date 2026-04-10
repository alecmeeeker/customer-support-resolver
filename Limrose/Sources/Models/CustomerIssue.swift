import Foundation
import GRDB

struct CustomerIssue: Codable, FetchableRecord, Identifiable {
    var id: Int64
    var emailId: Int64?
    var threadId: String?
    var issueType: String?
    var issueCategory: String?
    var issueSummary: String?
    var hasResolution: Bool
    var resolutionSummary: String?
    var fixInstructions: String?
    var similarityScore: Double?
    var basedOnIssues: String?
    var confidenceLevel: String?
    var createdAt: String?
    var updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case emailId = "email_id"
        case threadId = "thread_id"
        case issueType = "issue_type"
        case issueCategory = "issue_category"
        case issueSummary = "issue_summary"
        case hasResolution = "has_resolution"
        case resolutionSummary = "resolution_summary"
        case fixInstructions = "fix_instructions"
        case similarityScore = "similarity_score"
        case basedOnIssues = "based_on_issues"
        case confidenceLevel = "confidence_level"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

extension CustomerIssue: TableRecord {
    static let databaseTableName = "customer_issues_v2"
}
