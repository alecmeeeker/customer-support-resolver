import Foundation

final class FileWatcher {
    private var source: DispatchSourceFileSystemObject?
    private var fd: Int32 = -1

    func watch(path: String, onChange: @escaping () -> Void) {
        stop()

        // Ensure the file exists
        if !FileManager.default.fileExists(atPath: path) {
            FileManager.default.createFile(atPath: path, contents: nil)
        }

        fd = open(path, O_EVTONLY)
        guard fd >= 0 else { return }

        let src = DispatchSource.makeFileSystemObjectSource(
            fileDescriptor: fd,
            eventMask: [.write, .extend, .attrib, .rename],
            queue: .main
        )
        src.setEventHandler { onChange() }
        src.setCancelHandler { [weak self] in
            if let fd = self?.fd, fd >= 0 {
                close(fd)
            }
            self?.fd = -1
        }
        src.resume()
        self.source = src
    }

    func stop() {
        source?.cancel()
        source = nil
    }

    deinit {
        stop()
    }
}
