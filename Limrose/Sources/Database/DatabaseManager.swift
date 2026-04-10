import Foundation
import GRDB

@Observable
final class DatabaseManager {
    static let shared = DatabaseManager()

    private(set) var dbPool: DatabasePool?
    private var fileWatcher: DispatchSourceFileSystemObject?

    var databaseURL: URL {
        if let custom = UserDefaults.standard.string(forKey: "dataDirPath"), !custom.isEmpty {
            return URL(fileURLWithPath: custom).appendingPathComponent("limrose.db")
        }
        let appSupport = FileManager.default.urls(
            for: .applicationSupportDirectory, in: .userDomainMask
        ).first!
        let limroseDir = appSupport.appendingPathComponent("Limrose")
        return limroseDir.appendingPathComponent("limrose.db")
    }

    var dataDirURL: URL {
        databaseURL.deletingLastPathComponent()
    }

    func setup() throws {
        let dirURL = dataDirURL
        try FileManager.default.createDirectory(at: dirURL, withIntermediateDirectories: true)

        var config = Configuration()
        config.prepareDatabase { db in
            try db.execute(sql: "PRAGMA journal_mode=WAL")
            try db.execute(sql: "PRAGMA foreign_keys=ON")
        }

        dbPool = try DatabasePool(path: databaseURL.path, configuration: config)

        try dbPool?.write { db in
            try db.execute(sql: """
                CREATE TABLE IF NOT EXISTS customer_issues_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id INTEGER,
                    thread_id TEXT,
                    issue_type TEXT,
                    issue_category TEXT,
                    issue_summary TEXT,
                    has_resolution INTEGER DEFAULT 0,
                    resolution_summary TEXT,
                    fix_instructions TEXT,
                    similarity_score REAL,
                    based_on_issues TEXT,
                    confidence_level TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """)
        }
    }

    func startWatching(onChange: @escaping () -> Void) {
        let walPath = databaseURL.path + "-wal"

        // Touch the WAL file so it exists for watching
        if !FileManager.default.fileExists(atPath: walPath) {
            FileManager.default.createFile(atPath: walPath, contents: nil)
        }

        let fd = open(walPath, O_EVTONLY)
        guard fd >= 0 else { return }

        let source = DispatchSource.makeFileSystemObjectSource(
            fileDescriptor: fd,
            eventMask: [.write, .extend, .attrib],
            queue: .main
        )
        source.setEventHandler { onChange() }
        source.setCancelHandler { close(fd) }
        source.resume()
        self.fileWatcher = source
    }

    func stopWatching() {
        fileWatcher?.cancel()
        fileWatcher = nil
    }
}
