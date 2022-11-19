package LibTest;

import LibNet.NetLibrary;
import PetriObj.*;
import java.util.ArrayList;

public class TransportSystem {
  public static int NUM_RUNS = 10;
  public static int MODELLING_TIME = 600;

  public static void main(String[] args)
      throws ExceptionInvalidNetStructure, ExceptionInvalidTimeDelay {
    double earnedMoney = 0, meanWaitTime = 0;
    for (int runIdx = 0; runIdx < NUM_RUNS; ++runIdx) {
      var model = getModel();
      model.setIsProtokol(false);
      model.go(MODELLING_TIME);
      // Earned money
      earnedMoney +=
          model.getListObj().get(0).getNet().getListP()[6].getObservedMax() /
          (double)NUM_RUNS;
      // Mean wait time
      var firstCity = model.getListObj().get(0).getNet();
      var secondCity = model.getListObj().get(1).getNet();
      var numWaitedInQueues = (firstCity.getListP()[2].getMark() +
                               secondCity.getListP()[2].getMark() +
                               firstCity.getListP()[6].getObservedMax() / 20.0 +
                               firstCity.getListT()[3].getBuffer() +
                               firstCity.getListT()[3].getBuffer() +
                               secondCity.getListT()[3].getBuffer() +
                               secondCity.getListT()[3].getBuffer());
      var meanQueuesSize = firstCity.getListP()[2].getMean() +
                           secondCity.getListP()[2].getMean();
      meanWaitTime += (meanQueuesSize * MODELLING_TIME /
                       (double)Math.max(numWaitedInQueues, 1)) /
                      (double)NUM_RUNS;
    }
    System.out.printf("Earned money: %f\n", earnedMoney);
    System.out.printf("Mean wait time in queue: %f", meanWaitTime);
  }

  public static PetriObjModel getModel()
      throws ExceptionInvalidNetStructure, ExceptionInvalidTimeDelay {
    var petriObjects = new ArrayList<PetriSim>();
    // Petri objects
    petriObjects.add(new PetriSim(
        NetLibrary.CreateNetBusStation(0.5, 20.0, 30.0, 5.0, 30, 20, true)));
    petriObjects.add(new PetriSim(
        NetLibrary.CreateNetBusStation(0.5, 20.0, 30.0, 5.0, 30, 20, false)));
    // Connections
    petriObjects.get(1).getNet().getListP()[3] =
        petriObjects.get(0).getNet().getListP()[3]; // Lost Money
    petriObjects.get(1).getNet().getListP()[6] =
        petriObjects.get(0).getNet().getListP()[6]; // Earned Money
    petriObjects.get(1).getNet().getListP()[7] =
        petriObjects.get(0).getNet().getListP()[4]; // Empty Bus A in City 1
    petriObjects.get(1).getNet().getListP()[8] =
        petriObjects.get(0).getNet().getListP()[5]; // Empty Bus B in City 1
    petriObjects.get(0).getNet().getListP()[7] =
        petriObjects.get(1).getNet().getListP()[4]; // Empty Bus A in City 2
    petriObjects.get(0).getNet().getListP()[8] =
        petriObjects.get(1).getNet().getListP()[5]; // Empty Bus B in City 2
    return new PetriObjModel(petriObjects);
  }
}
