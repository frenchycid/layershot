import SwiftUI
import Observation

@Observable
public class AppState {
    public var moodboardPath: URL?
    public var moodboardImages: [URL] = []
    public var products: [Product] = []
    public var currentStep: PipelineStep = .idle
    public var pipelineLog: String = ""
    public var styleAnalysis: StyleAnalysis?
    public var masterPrompt: MasterPrompt?
    public var generatedImages: [GeneratedImage] = []
    public var isRunning: Bool = false
    public var outputPath: URL
    public var pythonPath: String = "/usr/bin/python3"
    public var projectPath: String

    public var isAuthenticated: Bool {
        get { UserDefaults.standard.bool(forKey: "isAuthenticated") }
        set { UserDefaults.standard.set(newValue, forKey: "isAuthenticated") }
    }

    public var claudeApiKey: String {
        get { UserDefaults.standard.string(forKey: "claudeApiKey") ?? "" }
        set { UserDefaults.standard.set(newValue, forKey: "claudeApiKey") }
    }

    public init() {
        let home    = FileManager.default.homeDirectoryForCurrentUser
        projectPath = home.appendingPathComponent("projects/layershot").path
        outputPath  = home.appendingPathComponent("projects/layershot/data/outputs")
    }

    public func addProduct(name: String, color: String) {
        products.append(Product(name: name, color: color))
    }

    public func removeProduct(at index: Int) {
        guard index < products.count else { return }
        products.remove(at: index)
    }

    public func appendLog(_ text: String) {
        pipelineLog += text
    }

    public func clearLog() {
        pipelineLog = ""
    }
}
