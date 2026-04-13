import SwiftUI

public struct ContentView: View {
    @Environment(AppState.self) private var appState

    public init() {}

    public var body: some View {
        NavigationSplitView {
            MoodboardPanel()
                .navigationSplitViewColumnWidth(min: 220, ideal: 240, max: 300)
        } content: {
            PipelinePanel()
                .navigationSplitViewColumnWidth(min: 400, ideal: 600)
        } detail: {
            GalleryPanel()
                .navigationSplitViewColumnWidth(min: 260, ideal: 340, max: 440)
        }
        .navigationTitle("LayerShot")
        .toolbar {
            ToolbarItem(placement: .navigation) {
                Image(systemName: "camera.aperture").foregroundStyle(.blue)
            }
            ToolbarItem(placement: .primaryAction) {
                if appState.isRunning {
                    ProgressView().scaleEffect(0.75).help("Pipeline en cours...")
                }
            }
            ToolbarItem(placement: .primaryAction) {
                SettingsLink {
                    Image(systemName: "gear")
                }
                .help("Paramètres")
            }
        }
    }
}
