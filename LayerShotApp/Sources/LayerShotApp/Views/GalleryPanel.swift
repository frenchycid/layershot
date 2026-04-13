import SwiftUI

public struct GalleryPanel: View {
    @Environment(AppState.self) private var appState
    @State private var selectedImage: GeneratedImage?
    @State private var columns: Int = 2
    @State private var filterView: String = "Tous"

    public init() {}

    private var views: [String] {
        ["Tous"] + Array(Set(appState.generatedImages.map { $0.view })).sorted()
    }

    private var filtered: [GeneratedImage] {
        filterView == "Tous" ? appState.generatedImages
            : appState.generatedImages.filter { $0.view == filterView }
    }

    public var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Image(systemName: "photo.stack").foregroundStyle(.purple)
                Text("Galerie").font(.headline)
                Spacer()
                Text("\(filtered.count) image\(filtered.count == 1 ? "" : "s")")
                    .font(.caption).foregroundStyle(.secondary)
                Stepper("", value: $columns, in: 1...4).labelsHidden().help("Colonnes")
            }
            .padding()

            // Filter bar
            if views.count > 1 {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 6) {
                        ForEach(views, id: \.self) { v in
                            Button(v) { filterView = v }
                                .buttonStyle(.bordered)
                                .tint(filterView == v ? .blue : .gray)
                                .controlSize(.small)
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.bottom, 6)
            }

            Divider()

            if filtered.isEmpty {
                ContentUnavailableView {
                    Label("Aucune image", systemImage: "photo.badge.plus")
                } description: {
                    Text("Lancez le pipeline pour voir les résultats ici")
                }
            } else {
                ScrollView {
                    LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: columns), spacing: 6) {
                        ForEach(filtered) { image in
                            ImageCard(image: image, isSelected: selectedImage?.id == image.id)
                                .onTapGesture { selectedImage = image }
                                .contextMenu {
                                    Button("Ouvrir dans Finder") {
                                        NSWorkspace.shared.activateFileViewerSelecting([image.url])
                                    }
                                    Button("Copier le chemin") {
                                        NSPasteboard.general.clearContents()
                                        NSPasteboard.general.setString(image.url.path, forType: .string)
                                    }
                                }
                        }
                    }
                    .padding(8)
                }
            }
        }
        .sheet(item: $selectedImage) { image in
            ImageDetailView(image: image)
        }
    }
}

struct ImageCard: View {
    let image: GeneratedImage
    let isSelected: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            AsyncImage(url: image.url) { img in
                img.resizable().aspectRatio(contentMode: .fit)
            } placeholder: {
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.gray.opacity(0.15))
                    .aspectRatio(1, contentMode: .fit)
                    .overlay { ProgressView().scaleEffect(0.6) }
            }
            .clipShape(RoundedRectangle(cornerRadius: 6))

            HStack(spacing: 4) {
                VStack(alignment: .leading, spacing: 1) {
                    Text("\(image.productName) • \(image.color)").font(.caption2).lineLimit(1)
                    Text("\(image.view) #\(image.variant)").font(.caption2).foregroundStyle(.secondary)
                }
                Spacer()
                if let score = image.qualityScore { ScoreBadge(score: score) }
            }
        }
        .padding(5)
        .background(isSelected ? Color.accentColor.opacity(0.1) : Color.clear)
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(isSelected ? Color.accentColor : Color.clear, lineWidth: 1.5)
        )
    }
}

struct ScoreBadge: View {
    let score: Double
    var color: Color { score >= 7 ? .green : (score >= 5 ? .orange : .red) }

    var body: some View {
        Text(String(format: "%.1f", score))
            .font(.caption2.bold()).foregroundStyle(.white)
            .padding(.horizontal, 5).padding(.vertical, 2)
            .background(color).clipShape(Capsule())
    }
}

struct ImageDetailView: View {
    let image: GeneratedImage
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 16) {
            HStack {
                Text(image.filename).font(.headline)
                Spacer()
                Button("Fermer") { dismiss() }.buttonStyle(.bordered).keyboardShortcut(.cancelAction)
            }

            AsyncImage(url: image.url) { img in
                img.resizable().aspectRatio(contentMode: .fit)
            } placeholder: { ProgressView() }
            .frame(maxHeight: 480)
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .shadow(radius: 4)

            HStack(spacing: 20) {
                Label(image.productName, systemImage: "shippingbox.fill")
                Label(image.color, systemImage: "paintpalette")
                Label("\(image.view) #\(image.variant)", systemImage: "camera")
                if let score = image.qualityScore {
                    Label(String(format: "%.1f / 10", score), systemImage: "star.fill")
                        .foregroundStyle(score >= 7 ? .green : (score >= 5 ? .orange : .red))
                }
            }
            .font(.callout)

            if let rec = image.recommendation {
                Text(rec.uppercased())
                    .font(.caption.bold())
                    .padding(.horizontal, 10).padding(.vertical, 4)
                    .background(rec == "keep" ? Color.green.opacity(0.15) : Color.orange.opacity(0.15))
                    .clipShape(Capsule())
            }

            HStack(spacing: 12) {
                Button { NSWorkspace.shared.activateFileViewerSelecting([image.url]) } label: {
                    Label("Finder", systemImage: "folder")
                }.buttonStyle(.bordered)

                Button { NSWorkspace.shared.open(image.url) } label: {
                    Label("Ouvrir", systemImage: "eye")
                }.buttonStyle(.bordered)

                Button {
                    let picker = NSSharingServicePicker(items: [image.url])
                    if let window = NSApp.keyWindow {
                        picker.show(relativeTo: .zero, of: window.contentView!, preferredEdge: .minY)
                    }
                } label: {
                    Label("Partager", systemImage: "square.and.arrow.up")
                }.buttonStyle(.borderedProminent)
            }
        }
        .padding(24).frame(minWidth: 620, minHeight: 500)
    }
}
