# BABEL: Cross-Species Semantic Primitive Alignment Fails with General Audio Encoders

## Abstract

BABEL studies whether animal vocalizations that serve the same communicative function across species can be aligned in a shared embedding space. We formalize a taxonomy of nine semantic primitives, including aerial alarm, ground alarm, food calls, affiliation, distress, mating, identity, and spatial location, and evaluate Phase 0 on 425 real audio signals spanning nine species. Two general-purpose baselines fail to recover cross-species functional equivalence. MFCC acoustic features obtain a primitive silhouette score of -0.185 and only 0.2% nearest-neighbor matches with the same primitive across different species. CLAP, a general audio-language model, performs worse, with a primitive silhouette score of -0.313 and 0.5% cross-species primitive nearest-neighbor matches. These negative results suggest that generic acoustic or internet-scale audio-language encoders do not yet represent the ethological semantics required for cross-species communication mapping, motivating bioacoustic domain-specific encoders and graph-based equivalence modeling.

## 1. Introduction - The Total Turing Test Gap

The Total Turing Test proposed that a genuinely general intelligence should not only manipulate language symbols, but also act and communicate across embodied cognitive systems. In 2026, this criterion remains technically underdeveloped for non-human communication. Machine learning systems can classify bird calls, cluster whale codas, and distinguish affective states in mammalian vocalizations, yet most work still follows an intra-species pipeline: collect signals from one taxon, train or adapt a model, and predict labels assigned by human observers.

BABEL asks a different question. Instead of treating each species as a separate decoding problem, it asks whether functionally equivalent signals across species occupy nearby regions of an embedding space. A vervet monkey eagle alarm, a prairie dog hawk alarm, and a crow aerial predator call differ in acoustics, morphology, and phylogeny. Ethologically, however, they instantiate a common function: warn conspecifics about an aerial predator.

This framing treats interspecies communication as an alignment problem rather than a translation problem. The target is not a human sentence for every call. The target is a graph of functional equivalences: which signals play comparable roles in perception, action, social coordination, and environmental response. The cultural metaphor is C-3PO, the protocol interpreter fluent across communicative systems.

The central claim of this Phase 0 report is narrow. General-purpose audio encoders - both acoustic feature baselines and audio-language models trained on broad internet audio - fail to capture cross-species semantic equivalences in animal communication. The failure establishes a negative baseline, clarifies what representation is missing, and motivates bioacoustic foundation models.

## 2. Related Work - ESP, CETI, Copenhagen, NeurIPS 2025

Recent work in animal communication has accelerated around large datasets, self-supervised audio learning, and multimodal annotation. The Earth Species Project's NatureLM-audio introduced a bioacoustic foundation model with explicit focus on animal sound understanding and zero-shot generalization. This is the closest architectural precedent for BABEL, although BABEL targets cross-species functional alignment rather than single-signal captioning or classification.

Project CETI has advanced the analysis of sperm whale communication, including work suggesting structured combinatorial patterns in codas. Such results deepen the case that non-human vocal systems may contain richer organization than previously assumed, but the technical target remains largely intra-species: model sperm whale signals as sperm whale communication.

Briefer and colleagues' Copenhagen 2025 work on affect classification across ungulates is an important cross-species precedent. Their reported 89.49% accuracy for emotion recognition across seven ungulate species demonstrates that machine learning can recover some shared biological signal across taxa. However, affective state classification is not the same as semantic primitive alignment. BABEL is concerned with functional communicative roles such as predator class, food discovery, affiliation, and identity.

The NeurIPS 2025 workshop on AI for non-human animal communication highlights related models such as WhaleLM, Dolph2Vec, and PrimateFace, as well as persistent challenges: scarce labels, domain shift, and weak grounding of human annotations. These efforts reveal the missing layer: a computable graph of equivalence across species.

Finally, the Total Turing Test literature frames the philosophical target. If intelligence is general across cognitive architectures, language technology should eventually bridge communicative systems with different bodies, ecological niches, and evolutionary histories. BABEL operationalizes part of that target as a measurable embedding problem.

## 3. Semantic Primitive Taxonomy

BABEL defines nine semantic primitives as candidate cross-species communicative functions. The taxonomy is intentionally functional rather than acoustic. A primitive is a role a signal plays in behavior, not a waveform class.

| ID | Function |
|---|---|
| ALARM_AERIAL | Alarm for aerial predators such as hawks or eagles |
| ALARM_GROUND | Alarm for terrestrial predators such as leopards or coyotes |
| ALARM_SNAKE | Alarm for snakes |
| FOOD_CALL | Food discovery or food localization call |
| CONTACT_AFFILIATION | Social contact, cohesion, or affiliative signaling |
| DISTRESS | Distress, separation, pain, or help-seeking call |
| MATING | Courtship or mating-related vocalization |
| IDENTITY | Individual or group identity signal |
| LOCATION | Spatial localization or position-related signal |

The working hypothesis is that a semantic bioacoustic encoder should partially factor out species-specific vocal morphology and preserve these functional roles. Phase 0 tests whether two general encoders already provide such a space.

## 4. Experimental Setup

The Phase 0 dataset contains 425 real `.wav` signals across nine species: vervet monkey, prairie dog, bottlenose dolphin, sperm whale, crow, elephant, pig, humpback whale, and songbird. Each example is assigned one of the nine semantic primitive labels. The dataset is a feasibility probe rather than a definitive benchmark: small, taxonomically broad, and optimized to test cross-species equivalence.

We evaluate three encoders in the experimental plan. The first two are complete and reported here. The third is pending and included only as the next planned comparison.

MFCC is an acoustic feature baseline. For each audio signal, we compute 40 MFCC means, 40 MFCC standard deviations, spectral centroid, and zero-crossing rate, producing an 82-dimensional representation. These features are expected to capture spectral shape and vocal morphology, not semantics.

CLAP is a general audio-language encoder, `laion/clap-htsat-unfused`, producing 512-dimensional audio embeddings. Because CLAP is trained on broad audio-text pairs, it tests whether internet-scale language alignment produces a semantic representation useful for animal communicative functions.

NatureLM-audio, `EarthSpeciesProject/NatureLM-audio`, is the planned domain-specific bioacoustic encoder. No NatureLM results are reported in this paper. Its inclusion defines the next experimental step.

For both completed encoders, embeddings are standardized with `StandardScaler`, reduced with UMAP using `n_neighbors=18`, `min_dist=0.08`, and cosine distance, and evaluated with two metrics. First, we compute silhouette score by semantic primitive and by species. Second, we run a nearest-neighbor cross-species test: for each signal, we identify its closest neighbor and count whether it has the same primitive, and whether it also belongs to a different species.

## 5. Results

| Encoder | Type | Dimensionality | Silhouette by primitive | Silhouette by species | Same primitive NN | Same primitive + different species NN |
|---|---:|---:|---:|---:|---:|---:|
| MFCC | Acoustic features | 82 | -0.185 | -0.043 | 84.0% (357/425) | 0.2% (1/425) |
| CLAP | General audio-language | 512 | -0.313 | -0.130 | 94.6% (402/425) | 0.5% (2/425) |
| NatureLM-audio | Bioacoustic foundation model | 1024 expected | pending | pending | pending | pending |

Both completed encoders fail the core cross-species primitive test. MFCC features produce a negative primitive silhouette score, indicating that primitive labels do not form coherent clusters in the UMAP space. The high same-primitive nearest-neighbor rate of 84.0% is misleading without the cross-species constraint: almost all of that signal is within species. Only one out of 425 signals has a nearest neighbor from another species with the same primitive.

CLAP performs worse on primitive silhouette, with a score of -0.313. This suggests that broad audio-language pretraining does not automatically recover ethological function. Its cross-species same-primitive nearest-neighbor rate is 0.5%, only two of 425 examples. The result is not evidence against semantic structure in animal communication; it is evidence that a general human-audio captioning representation does not expose that structure in this setting.

## 6. Discussion

The negative results are consistent with the distinction between acoustic similarity and communicative equivalence. Signals with the same functional role may be acoustically distant because they are produced by different vocal tracts, transmitted through different environments, and shaped by different receivers. A dolphin whistle, a crow call, and a vervet bark can participate in social coordination or alarm behavior while sharing little spectral morphology.

MFCCs fail for the expected reason: they primarily encode local spectral and temporal shape. They are useful for measuring the surface of the signal, but BABEL's target lies one abstraction level above that surface. The nearest-neighbor results show that MFCC space can preserve local regularities, including repeated patterns within a species and primitive, while still failing to bridge species boundaries.

CLAP's failure is more informative. Audio-language training introduces broad semantic supervision, but the supervision is mostly human-centered and internet-derived. It can distinguish "animal sound," "bird call," or "high-pitched chirp," but those labels are not equivalent to predator class, food discovery, identity, or affiliative function. General audio-language semantics may reinforce perceptual categories available to human annotators rather than ethological categories available to animal receivers.

These findings imply that cross-species animal communication requires representations grounded in bioacoustic context: species behavior, ecological function, call usage, and receiver response. A useful encoder must learn that two signals can be functionally equivalent despite different waveforms, and that two acoustically similar signals can differ in meaning depending on context.

The broader implication is methodological. Cross-species alignment should not be evaluated only through classification accuracy within a species. It needs explicit tests for functional equivalence across species, including nearest-neighbor retrieval, primitive clustering, and graph connectivity. BABEL's Phase 0 provides a compact diagnostic for this purpose.

## 7. Next Steps - NatureLM-audio and BabelGraph

The next experiment is to run the same pipeline with NatureLM-audio on a GPU instance using 8-bit quantization. The hypothesis is not included as a result here; it is a falsifiable next test. If a bioacoustic encoder improves primitive silhouette and cross-species nearest-neighbor retrieval, it would support the claim that ethological pretraining captures functional structure absent from general encoders.

If such signal appears, BABEL will construct BabelGraph: a graph whose nodes are species-specific signals and whose edges represent embedding similarity, shared primitive labels, and cross-species equivalence candidates. This would enable C-3PO-style lookup: given a signal in one species, retrieve functionally analogous signals in other species.

If NatureLM also fails, the result would still be useful. It would imply that current foundation models lack the supervision required for functional semantics and that BABEL needs contrastive fine-tuning on explicitly aligned primitive pairs.

## References

1. Earth Species Project. NatureLM-audio: an audio-language foundation model for bioacoustics. ICLR 2025; arXiv:2411.07186.
2. Briefer, E. F., et al. Cross-species machine learning for emotion recognition in ungulate vocalizations. Copenhagen 2025.
3. Project CETI / UC Berkeley. Recent work on sperm whale coda structure and phonetic organization, 2025.
4. Harnad, S. The Total Turing Test. Springer, 1991.
5. NeurIPS 2025 Workshop on AI for Non-Human Animal Communication. Workshop proceedings and model reports including WhaleLM, Dolph2Vec, and PrimateFace.
